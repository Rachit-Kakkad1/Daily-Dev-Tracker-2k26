# 📓 Daily Dev Tracker

> A real-time developer activity journal — auto-generated from actual GitHub commits across all my repos.

Every entry here is **100% real**. No fake commits. No automation tricks.
This tracker wakes up the moment I push to any of my projects and logs exactly what I did.

---

## 🔧 How It Works

```
You push to any repo (COS, portfolio, LeetCode...)
         │
         ▼
notify-tracker.yml fires a repository_dispatch event
         │
         ▼
daily-dev-tracker wakes up
         │
         ▼
GitHub API fetches ALL commits you made today across ALL repos
         │
         ▼
Logs them into daily-log.md, updates stats.md & progress.json
         │
         ▼
One clean, real commit to this repo
```

---

## 📁 Files

| File | Purpose |
|------|---------|
| `logs/daily-log.md` | Day-by-day journal of all commits |
| `logs/stats.md` | Running stats: streak, total commits, avg/day |
| `logs/progress.json` | Machine-readable history for future tooling |
| `scripts/generate_log.py` | Core script that talks to GitHub API |
| `.github/workflows/daily-tracker.yml` | Tracker repo workflow (listens for dispatch) |
| `notify-tracker-workflow/notify-tracker.yml` | Drop this into every other repo |

---

## ⚙️ Setup

### Step 1 — Create this repo
Create a new public/private repo named `daily-dev-tracker` on GitHub.
Push all files from here into it.

### Step 2 — Create a Personal Access Token (PAT)
1. Go to **GitHub → Settings → Developer Settings → Personal Access Tokens → Fine-grained tokens**
2. Create a token with these permissions:
   - **Contents**: Read & Write (for all repos you want to track)
   - **Actions**: Read & Write
   - **Metadata**: Read
3. Copy the token.

### Step 3 — Add Secrets to ALL your repos
Go to **each repo → Settings → Secrets and variables → Actions → New secret**

Add these three secrets to **every repo** (including this tracker repo):

| Secret Name | Value |
|-------------|-------|
| `GH_PAT` | Your Personal Access Token |
| `GH_USERNAME` | `Rachit-Kakkad1` |
| `GH_EMAIL` | Your GitHub email |

### Step 4 — Add notify workflow to every other repo
Copy `notify-tracker-workflow/notify-tracker.yml` into:
```
your-other-repo/.github/workflows/notify-tracker.yml
```
Do this for: COS, portfolio, LeetCode, Jarvis, ThreatLens — every repo you work in.

### Step 5 — Done!
Push any commit to any tracked repo.
Watch `daily-dev-tracker` update itself in ~30 seconds.

---

## 📊 Stats

See [`logs/stats.md`](logs/stats.md) for live stats.

---

*Built by Rachit Kakkad · Powered by GitHub Actions + Python*
