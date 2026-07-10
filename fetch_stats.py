"""Fetch GitHub stats for the profile card into stats.json.

Needs GITHUB_TOKEN (or GH_TOKEN) in the environment. Public data only:
repos/stars/followers, all-time commit contributions, and LoC summed from
per-repo contributor stats (additions/deletions authored by LOGIN).
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

LOGIN = "King0James0"
HERE = os.path.dirname(os.path.abspath(__file__))
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
if not TOKEN:
    sys.exit("GITHUB_TOKEN not set")


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


def rest(path):
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={"Authorization": f"bearer {TOKEN}", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req) as r:
        body = r.read()
        return r.status, (json.loads(body) if body else None)


USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100) {
      totalCount
      nodes { name isFork stargazerCount }
    }
    repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, PULL_REQUEST, ISSUE, REPOSITORY]) {
      totalCount
    }
  }
}
"""

COMMITS_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
    }
  }
}
"""


def main():
    user = gql(USER_QUERY, {"login": LOGIN})["user"]
    created = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    repos = user["repositories"]
    stars = sum(n["stargazerCount"] for n in repos["nodes"])

    commits = 0
    now = datetime.now(timezone.utc)
    for year in range(created.year, now.year + 1):
        frm = max(created, datetime(year, 1, 1, tzinfo=timezone.utc))
        to = min(now, datetime(year, 12, 31, 23, 59, 59, tzinfo=timezone.utc))
        cc = gql(COMMITS_QUERY, {"login": LOGIN, "from": frm.isoformat(), "to": to.isoformat()})
        commits += cc["user"]["contributionsCollection"]["totalCommitContributions"]

    loc_add = loc_del = 0
    for node in repos["nodes"]:
        if node["isFork"]:
            continue
        data = None
        for attempt in range(6):
            status, data = rest(f"/repos/{LOGIN}/{node['name']}/stats/contributors")
            if status == 200 and data is not None:
                break
            time.sleep(4)  # 202 = GitHub still computing the stats
        if not isinstance(data, list):
            print(f"warn: no contributor stats for {node['name']}", file=sys.stderr)
            continue
        for contributor in data:
            author = contributor.get("author") or {}
            if (author.get("login") or "").lower() != LOGIN.lower():
                continue
            for week in contributor["weeks"]:
                loc_add += week["a"]
                loc_del += week["d"]

    stats = {
        "created_at": user["createdAt"],
        "repos": repos["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "stars": stars,
        "followers": user["followers"]["totalCount"],
        "commits": commits,
        "loc_add": loc_add,
        "loc_del": loc_del,
        "fetched_at": now.strftime("%Y-%m-%d"),
    }
    with open(os.path.join(HERE, "stats.json"), "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
        f.write("\n")
    print(json.dumps(stats))


if __name__ == "__main__":
    main()
