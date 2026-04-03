#!/usr/bin/env python3
"""
generate_log.py
Fetches all of today's commits across all of Rachit's repos
and appends a clean entry to the daily dev log.
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
import random

# ── Config ────────────────────────────────────────────────────────────────────

GH_PAT      = os.environ["GH_PAT"]
GH_USERNAME = os.environ["GH_USERNAME"]

# Optional: passed in when triggered via repository_dispatch
TRIGGER_REPO      = os.environ.get("TRIGGER_REPO", "")
TRIGGER_SHA       = os.environ.get("TRIGGER_SHA", "")
TRIGGER_MESSAGE   = os.environ.get("TRIGGER_MESSAGE", "")
TRIGGER_AUTHOR    = os.environ.get("TRIGGER_AUTHOR", "")
TRIGGER_TIMESTAMP = os.environ.get("TRIGGER_TIMESTAMP", "")

IST = timezone(timedelta(hours=5, minutes=30))
TODAY_IST = datetime.now(IST).date()

HEADERS = {
    "Authorization": f"Bearer {GH_PAT}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

# ── Files ─────────────────────────────────────────────────────────────────────

LOG_FILE      = "logs/daily-log.md"
PROGRESS_FILE = "logs/progress.json"
STATS_FILE    = "logs/stats.md"
COMMIT_MSG    = "/tmp/commit_msg.txt"

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_all_repos():
    """Return all repos owned by the user."""
    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/user/repos",
            headers=HEADERS,
            params={"per_page": 100, "page": page, "affiliation": "owner"},
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        page += 1
    return repos


def get_today_commits(repo_full_name):
    """Return commits made today (IST) in a given repo."""
    since = datetime.combine(TODAY_IST, datetime.min.time()).replace(tzinfo=IST).isoformat()
    until = datetime.combine(TODAY_IST, datetime.max.time()).replace(tzinfo=IST).isoformat()
    try:
        r = requests.get(
            f"https://api.github.com/repos/{repo_full_name}/commits",
            headers=HEADERS,
            params={"author": GH_USERNAME, "since": since, "until": until, "per_page": 50},
        )
        if r.status_code == 409:  # empty repo
            return []
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"  ⚠️  Could not fetch commits for {repo_full_name}: {e}")
        return []


def classify_repo(repo_name):
    """Map repo name to a human-readable category."""
    name = repo_name.lower()
    if any(k in name for k in ["leetcode", "dsa", "algo", "cp", "competitive"]):
        return "DSA / Competitive Programming"
    if any(k in name for k in ["portfolio", "personal-site", "website"]):
        return "Portfolio"
    if any(k in name for k in ["cos", "mindmesh", "cognitive"]):
        return "COS — Cognitive Operating System"
    if any(k in name for k in ["worksense", "work-sense"]):
        return "WorkSense (COS B2B Layer)"
    if any(k in name for k in ["jarvis", "voice", "assistant"]):
        return "Jarvis — AI Voice Assistant"
    if any(k in name for k in ["threatlens", "threat"]):
        return "ThreatLens"
    if any(k in name for k in ["agricert", "agri"]):
        return "AgriCert"
    if any(k in name for k in ["lifelens", "life-lens"]):
        return "LifeLens AI"
    if any(k in name for k in ["fleet", "fleetflow"]):
        return "FleetFlow"
    if any(k in name for k in ["tracker", "daily-dev"]):
        return None  # skip self
    return repo_name  # fallback: use raw name


def summarise_commit(message):
    """Return a clean one-liner from the commit message."""
    first_line = message.strip().splitlines()[0]
    return first_line[:120]  # cap length


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {
        "total_commits": 0,
        "total_days_active": 0,
        "repos_touched": [],
        "streak": 0,
        "last_active_date": "",
        "history": {}
    }


def save_progress(data):
    os.makedirs("logs", exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def pick_commit_message(repo_buckets, total):
    """Generate a conventional-commit style message for the tracker commit."""
    date_str = TODAY_IST.strftime("%d %b %Y")
    if total == 0:
        return f"chore: daily check-in for {date_str} — no commits yet"

    touched = list(repo_buckets.keys())
    if len(touched) == 1:
        return f"docs: log {total} commit(s) on {touched[0]} · {date_str}"
    if len(touched) == 2:
        return f"docs: activity across {touched[0]} & {touched[1]} · {date_str}"

    picks = random.sample([
        f"docs: daily dev log — {total} commits across {len(touched)} repos · {date_str}",
        f"chore: update journal · {date_str} · {total} commit(s)",
        f"docs: log activity for {date_str} ({len(touched)} repos touched)",
        f"chore: dev tracker update · {date_str}",
        f"docs: {date_str} — {total} commits logged across {', '.join(touched[:2])} + more",
    ], 1)
    return picks[0]


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print(f"📅 Fetching activity for {TODAY_IST} (IST)...")

    # 1. Gather all repos
    repos = get_all_repos()
    print(f"   Found {len(repos)} repos to scan.")

    # 2. Fetch today's commits per repo
    repo_buckets = {}  # category → list of commit summaries
    total_commits = 0

    for repo in repos:
        full_name = repo["full_name"]
        category  = classify_repo(repo["name"])
        if category is None:
            continue  # skip the tracker repo itself

        commits = get_today_commits(full_name)
        if not commits:
            continue

        if category not in repo_buckets:
            repo_buckets[category] = []

        for c in commits:
            msg = c["commit"]["message"]
            sha = c["sha"][:7]
            ts  = dateparser.parse(c["commit"]["author"]["date"]).astimezone(IST)
            time_str = ts.strftime("%I:%M %p")
            repo_buckets[category].append({
                "sha": sha,
                "message": summarise_commit(msg),
                "time": time_str,
                "repo": full_name,
            })
            total_commits += 1

    print(f"   Total commits found today: {total_commits}")

    # 3. Build the markdown log entry
    os.makedirs("logs", exist_ok=True)
    date_heading = TODAY_IST.strftime("%A, %d %B %Y")
    lines = []
    lines.append(f"\n---\n")
    lines.append(f"\n## 📅 {date_heading}\n")

    if not repo_buckets:
        lines.append(f"> _No commits recorded today. Rest day or early morning check-in._\n")
    else:
        lines.append(f"> **{total_commits} commit(s)** across **{len(repo_buckets)} project(s)** today.\n")
        for category, commits in repo_buckets.items():
            lines.append(f"\n### 🔧 {category}\n")
            for c in commits:
                lines.append(f"- `{c['sha']}` · **{c['time']}** — {c['message']}\n")

    lines.append(f"\n_Last updated: {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}_\n")

    # 4. Append to daily-log.md
    log_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a") as f:
        if not log_exists:
            f.write("# 📓 Rachit's Daily Dev Log\n")
            f.write("> Auto-generated from real GitHub activity. Every entry is a real commit.\n")
        f.writelines(lines)

    print(f"   ✅ Appended entry to {LOG_FILE}")

    # 5. Update progress.json
    progress = load_progress()
    today_str = str(TODAY_IST)

    progress["total_commits"] += total_commits
    progress["history"][today_str] = {
        "commits": total_commits,
        "repos": list(repo_buckets.keys()),
    }

    # Streak logic
    yesterday = str(TODAY_IST - timedelta(days=1))
    if progress["last_active_date"] == yesterday and total_commits > 0:
        progress["streak"] += 1
    elif total_commits > 0:
        progress["streak"] = 1

    if total_commits > 0:
        progress["last_active_date"] = today_str
        if today_str not in [str(TODAY_IST)]:
            progress["total_days_active"] += 1

    for cat in repo_buckets:
        if cat not in progress["repos_touched"]:
            progress["repos_touched"].append(cat)

    save_progress(progress)
    print(f"   ✅ Updated {PROGRESS_FILE}")

    # 6. Regenerate stats.md
    total_days = len(progress["history"])
    avg = round(progress["total_commits"] / total_days, 1) if total_days else 0
    most_active = max(progress["history"].items(), key=lambda x: x[1]["commits"], default=(today_str, {"commits": 0}))

    stats_lines = [
        "# 📊 Dev Stats\n\n",
        f"> Auto-updated every time a commit is pushed to any tracked repo.\n\n",
        f"| Metric | Value |\n",
        f"|--------|-------|\n",
        f"| 🔥 Current Streak | **{progress['streak']} day(s)** |\n",
        f"| 📦 Total Commits Logged | **{progress['total_commits']}** |\n",
        f"| 📅 Active Days | **{total_days}** |\n",
        f"| 📈 Avg Commits/Day | **{avg}** |\n",
        f"| 🏆 Most Active Day | **{most_active[0]}** ({most_active[1]['commits']} commits) |\n",
        f"| 🗂️ Projects Touched | **{len(progress['repos_touched'])}** |\n\n",
        f"## Projects\n\n",
    ]
    for repo in progress["repos_touched"]:
        stats_lines.append(f"- {repo}\n")
    stats_lines.append(f"\n_Last updated: {datetime.now(IST).strftime('%d %b %Y, %I:%M %p IST')}_\n")

    with open(STATS_FILE, "w") as f:
        f.writelines(stats_lines)

    print(f"   ✅ Regenerated {STATS_FILE}")

    # 7. Write commit message for the workflow to use
    commit_msg = pick_commit_message(repo_buckets, total_commits)
    with open(COMMIT_MSG, "w") as f:
        f.write(commit_msg)

    print(f"\n🚀 Commit message: {commit_msg}")
    print("✅ Done.")


if __name__ == "__main__":
    main()
