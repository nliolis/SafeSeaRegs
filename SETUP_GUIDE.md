# SafeSea Auto-Update Robot — Setup Guide

This sets up a free robot that, **once a day**, checks NOAA's official Federal Register
for tuna/shark rule changes. When it finds one, it **texts your phone** and opens an
approval page. You tap **approve**, and your app updates itself. Nothing changes until you say so.

Written for someone who has never touched code. Follow it top to bottom. ~20 minutes, once.

---

## What you'll end up with
- A daily check of NOAA's official rule-change feed (free, government source).
- A **text to your AT&T phone** when a tuna/shark rule changes, with the full before → after.
- A one-tap **approve / reject**. Approve = your app refreshes itself. Reject = nothing happens.

## What it costs
- GitHub: **free**. Federal Register: **free**.
- The AI that reads the legal notice: an Anthropic key — **pennies**, only when a rule actually changes.
- Texts via AT&T email-to-text: **free** (works for most people; can occasionally be filtered — if it gets flaky, ask me to switch you to the $1/month rock-solid option).

## What it does NOT cover
- **State** rules (e.g. Florida mahi) — those don't go through the Federal Register, so they stay manual.
- Heads-up: the AI reads legal text and is usually right, but you are the approver — glance at the before/after before you tap approve. The app keeps its "not legal advice — verify with NOAA" note.

---

## STEP 1 — Make a free GitHub account
1. Go to **github.com** → **Sign up**. Pick a username, email, password. (Free plan is fine.)
2. Verify your email when they send the link.

## STEP 2 — Create the project ("repository")
1. Top-right **+** → **New repository**.
2. Repository name: `safesea-regs`. Set it to **Public** (free Actions). Click **Create repository**.
3. On the new page, click **uploading an existing file**.
4. Download the file **safesea-autoupdate-kit.zip** I gave you and unzip it on your computer.
5. Drag ALL the unzipped items into the upload box — including the `.github` folder, `state` folder, `watcher.py`, `apply.py`, and `regs.json`. Then **Commit changes**.
   (If the `.github` folder won't drag, see "Manual file creation" at the bottom.)

## STEP 3 — Get the AI key (pennies)
1. Go to **console.anthropic.com** → sign up/log in.
2. Add a small amount of credit ($5 lasts a very long time here).
3. **API Keys** → **Create Key** → copy the key (starts with `sk-ant-...`). Keep it handy.

## STEP 4 — Make a Gmail "app password" (so the robot can text you)
*(Any Gmail works. This lets the robot send the text; it never sees your normal password.)*
1. Your Google account needs **2-Step Verification** ON (myaccount.google.com → Security).
2. Then go to **myaccount.google.com/apppasswords**, name it "SafeSea", and copy the **16-character** password it gives you.

## STEP 5 — Tell the robot your secrets
In your `safesea-regs` repo: **Settings** → (left side) **Secrets and variables** → **Actions** → **New repository secret**. Add these one at a time (Name, then Value):

| Name | Value |
|---|---|
| `ANTHROPIC_API_KEY` | your `sk-ant-...` key from Step 3 |
| `MAIL_USERNAME` | your full Gmail address |
| `MAIL_PASSWORD` | the 16-char app password from Step 4 |
| `SMS_TO` | `yourphonenumber@txt.att.net` (e.g. `5165551234@txt.att.net`) |

(Optional) `AI_MODEL` — leave it out unless I tell you a newer model name.

## STEP 6 — Turn it on and test
1. In the repo, click the **Actions** tab. If it asks, click **I understand my workflows, enable them**.
2. Click **Watch NOAA regs** (left) → **Run workflow** → **Run workflow** (green button). This runs it once now.
3. Wait ~1 minute. If there's been a recent NOAA change it'll **text you** and create an **Issue**.
   (If nothing's changed recently, that's normal — it just means no news. It now runs itself every day.)

## STEP 7 — Point your app at the live file
1. In the repo, open **regs.json**, click **Raw** (top-right of the file). Copy that URL
   (looks like `https://raw.githubusercontent.com/YOURNAME/safesea-regs/main/regs.json`).
2. In the SafeSea app: **Regs** tab → **↻ Auto-Update Feed** → paste the URL → **Save**.
   You'll see "✓ Auto-updated from your Federal Register feed." Done.

---

## How a real update will feel
1. NOAA changes a rule. Within a day you get a text:
   *"SafeSea - NOAA rule change. Bluefin comm: 3 fish/day -> 1 fish/day (eff Jul 3). Approve: <link>"*
2. Tap the link → it opens the **Issue** on GitHub showing the full before → after and the exact change.
3. Add a comment that just says **approve** (or **reject**). Send it.
4. Approve → the robot updates `regs.json` and closes the issue. Your app shows the new rule next time it opens.

---

## Manual file creation (only if dragging the `.github` folder failed)
GitHub web sometimes hides folders that start with a dot. If so, create files by hand:
1. In the repo: **Add file → Create new file**.
2. In the filename box type the FULL path, e.g. `.github/workflows/watch-regs.yml` (the slashes make the folders).
3. Paste that file's contents (open it from the unzipped kit in any text editor), **Commit**.
4. Repeat for `.github/workflows/apply-approval.yml`. The other files (`watcher.py`, `apply.py`, `regs.json`, `state/processed.json`) can be uploaded normally.

## If something doesn't work
Send me what the **Actions** tab shows in red (click the failed run → the step with the X). I built this
but can't run your live accounts from here, so the first run occasionally needs a small tweak — I'll fix it fast.
