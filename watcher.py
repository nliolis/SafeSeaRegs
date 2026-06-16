#!/usr/bin/env python3
"""
SafeSea reg watcher.
Runs daily on GitHub Actions. Checks the Federal Register for new NOAA Highly
Migratory Species rule changes (bluefin/yellowfin/bigeye/mahi/sharks), asks Claude
to extract the before -> after change and a regs.json patch, opens a GitHub issue
for your approval, and texts you a summary. Nothing goes live until you reply.
Standard library only (no pip installs).
"""
import os, json, datetime, urllib.request, urllib.parse, smtplib, ssl
from email.mime.text import MIMEText

FR_API   = "https://www.federalregister.gov/api/v1/documents.json"
TERM     = "Atlantic Highly Migratory Species"
AGENCY   = "national-oceanic-and-atmospheric-administration"
STATE    = "state/processed.json"

REPO   = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN  = os.environ.get("GITHUB_TOKEN", "")
AIKEY  = os.environ.get("ANTHROPIC_API_KEY", "")
MUSER  = os.environ.get("MAIL_USERNAME", "")
MPASS  = os.environ.get("MAIL_PASSWORD", "")
SMS_TO = os.environ.get("SMS_TO", "")            # e.g. 5551234567@txt.att.net
MODEL  = os.environ.get("AI_MODEL", "claude-3-5-sonnet-20241022")

def get_json(url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers=headers or {"User-Agent": "SafeSea-Watcher"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def load_state():
    try:
        with open(STATE) as f: return json.load(f)
    except Exception:
        return {"processed": [], "last_check": None}

def save_state(s):
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    s["processed"] = s["processed"][-300:]  # keep it small
    with open(STATE, "w") as f: json.dump(s, f, indent=2)

def fetch_recent(since):
    params = {
        "conditions[term]": TERM,
        "conditions[agencies][]": AGENCY,
        "order": "newest", "per_page": "20",
        "fields[]": ["document_number","title","abstract","publication_date","html_url","type","effective_on"],
    }
    qs = urllib.parse.urlencode(params, doseq=True)
    if since: qs += "&conditions[publication_date][gte]=" + since
    return get_json(FR_API + "?" + qs)

def ai_extract(doc):
    if not AIKEY: return None
    prompt = (
        "You maintain a fishing-regulations data file for these species ids: "
        "bluefin, yellowfin, bigeye, mahi, sharks; and modes: rec, charter, comm.\n"
        "Here is a NOAA Federal Register notice.\n"
        "TITLE: " + doc["title"] + "\nABSTRACT: " + (doc.get("abstract") or "") + "\n\n"
        "If it is a retention-limit change, closure, or reopening for one of those species, "
        "return ONLY this JSON (no prose):\n"
        '{"relevant":true,"species":"<id>","mode":"rec|charter|comm","before":"...",'
        '"after":"...","effective":"YYYY-MM-DD or text","summary":"one sentence",'
        '"patch":{"species":{"<id>":{"<mode>":{"limit":"...","statusLbl":"...","status":"open|closed|partial"}}}}}\n'
        "Otherwise return {\"relevant\":false}."
    )
    body = json.dumps({"model": MODEL, "max_tokens": 700,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    data = get_json("https://api.anthropic.com/v1/messages", headers={
        "x-api-key": AIKEY, "anthropic-version": "2023-06-01", "content-type": "application/json"
    }, data=body)
    txt = "".join(b.get("text","") for b in data.get("content", []) if b.get("type")=="text").strip()
    if txt.startswith("```"): txt = txt.strip("`"); txt = txt[4:] if txt.lower().startswith("json") else txt
    i, j = txt.find("{"), txt.rfind("}")
    try: return json.loads(txt[i:j+1])
    except Exception: return None

def create_issue(title, body):
    data = json.dumps({"title": title, "body": body, "labels": ["regs-update"]}).encode()
    return get_json("https://api.github.com/repos/%s/issues" % REPO, headers={
        "Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
        "User-Agent": "SafeSea-Watcher", "Content-Type": "application/json"}, data=data)

def send_text(summary, url):
    if not (MUSER and MPASS and SMS_TO): return
    msg = MIMEText("SafeSea - NOAA rule change\n" + summary + "\nApprove: " + url)
    msg["From"], msg["To"], msg["Subject"] = MUSER, SMS_TO, "SafeSea"
    ctx = ssl.create_default_context()
    with smtplib.SMTP("smtp.gmail.com", 587) as s:
        s.starttls(context=ctx); s.login(MUSER, MPASS)
        s.sendmail(MUSER, [SMS_TO], msg.as_string())

def main():
    st = load_state()
    since = st.get("last_check") or (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
    docs = (fetch_recent(since).get("results") or [])
    new = [d for d in docs if d["document_number"] not in st["processed"]]
    flagged = 0
    for d in new:
        st["processed"].append(d["document_number"])
        ext = ai_extract(d)
        if not ext or not ext.get("relevant"): continue
        summary = "%s %s: %s -> %s (eff %s)" % (
            str(ext.get("species","?")).title(), ext.get("mode",""),
            ext.get("before","?"), ext.get("after","?"), ext.get("effective","?"))
        body = ("**" + ext.get("summary","") + "**\n\n"
                "- **Species:** " + str(ext.get("species")) + "  \n"
                "- **Category:** " + str(ext.get("mode")) + "  \n"
                "- **Before:** " + str(ext.get("before")) + "  \n"
                "- **After:** " + str(ext.get("after")) + "  \n"
                "- **Effective:** " + str(ext.get("effective")) + "  \n"
                "- **Source:** " + d["html_url"] + " (" + d["document_number"] + ")\n\n"
                "Reply **approve** to apply this to regs.json, or **reject** to discard.\n\n"
                "```json\n" + json.dumps(ext.get("patch", {}), indent=2) + "\n```")
        issue = create_issue("[Regs] " + summary, body)
        send_text(summary, issue.get("html_url",""))
        flagged += 1
    st["last_check"] = datetime.date.today().isoformat()
    save_state(st)
    print("Checked %d docs, %d new, %d change(s) flagged for approval." % (len(docs), len(new), flagged))

if __name__ == "__main__":
    main()
