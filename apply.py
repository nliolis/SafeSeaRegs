#!/usr/bin/env python3
"""Apply an approved change: pull the JSON patch out of the issue body, merge it
into regs.json, and bump the verified date. Run by the approval workflow."""
import os, json, re, datetime, urllib.request

REGS  = "regs.json"
REPO  = os.environ.get("GITHUB_REPOSITORY", "")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ISSUE = os.environ.get("ISSUE_NUMBER", "")

def gh(url):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + TOKEN, "Accept": "application/vnd.github+json",
        "User-Agent": "SafeSea-Apply"})
    with urllib.request.urlopen(req, timeout=30) as r: return json.load(r)

def deep_merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): deep_merge(a[k], v)
        else: a[k] = v
    return a

def main():
    issue = gh("https://api.github.com/repos/%s/issues/%s" % (REPO, ISSUE))
    m = re.search(r"```json\s*(\{.*?\})\s*```", issue.get("body",""), re.S)
    if not m:
        print("No JSON patch found; nothing to apply."); return
    patch = json.loads(m.group(1))
    with open(REGS) as f: regs = json.load(f)
    deep_merge(regs, patch)
    regs["verified"] = datetime.date.today().isoformat()
    with open(REGS, "w") as f: json.dump(regs, f, indent=2)
    print("regs.json updated from issue #%s" % ISSUE)

if __name__ == "__main__":
    main()
