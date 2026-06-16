#!/usr/bin/env python3
import os, json, re, datetime, subprocess, urllib.request

REGS  = "regs.json"
REPO  = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ISSUE = os.environ.get("ISSUE_NUMBER", "")
OWNER = os.environ.get("REPO_OWNER", "")
ACTOR = os.environ.get("ACTOR", "")
COMMENT = os.environ.get("COMMENT_BODY", "")

def api(method, path, payload=None):
    url = "https://api.github.com/repos/%s/%s" % (REPO, path)
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
        "User-Agent": "SafeSea-Apply", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def say(msg):
    try: api("POST", "issues/%s/comments" % ISSUE, {"body": msg})
    except Exception as e: print("comment failed:", e)

def close():
    try: api("PATCH", "issues/%s" % ISSUE, {"state": "closed"})
    except Exception as e: print("close failed:", e)

def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep_merge(a[k], v)
        else: a[k] = v
    return a

def main():
    if ACTOR and OWNER and ACTOR != OWNER:
        print("Not owner; ignoring."); return
    c = re.sub(r"\s+", "", COMMENT).lower()
    if c == "reject":
        say("Rejected. Nothing changed."); close(); return
    if c != "approve":
        print("Not approve/reject; ignoring."); return
    issue = api("GET", "issues/%s" % ISSUE)
    m = re.search(r"```json\s*(\{.*?\})\s*```", issue.get("body", ""), re.S)
    if not m:
        say("Couldn't find a change to apply in this issue."); return
    patch = json.loads(m.group(1))
    with open(REGS) as f: regs = json.load(f)
    deep_merge(regs, patch)
    regs["verified"] = datetime.date.today().isoformat()
    with open(REGS, "w") as f: json.dump(regs, f, indent=2)
    subprocess.run(["git", "config", "user.name", "safesea-bot"], check=False)
    subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=False)
    subprocess.run(["git", "add", "regs.json"], check=False)
    subprocess.run(["git", "commit", "-m", "apply approved reg change (#%s)" % ISSUE], check=False)
    subprocess.run(["git", "push"], check=False)
    say("Applied to regs.json. Your app updates on next launch.")
    close()
    print("Done.")

if __name__ == "__main__":
    main()
