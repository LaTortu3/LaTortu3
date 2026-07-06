import os
import re
import requests
from datetime import datetime

# Read token
TOKEN = os.getenv("GH_TOKEN")
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

if not TOKEN:
    if IS_GITHUB_ACTIONS:
        raise ValueError("GH_TOKEN is missing in the GitHub Actions environment.")
    else:
        print("GH_TOKEN is missing, falling back to mock data.")
        MOCK_DATA = True
else:
    MOCK_DATA = False

GRAPHQL_URL = "https://api.github.com/graphql"
QUERY = """
{
  viewer {
    repositories(
      first: 100
      orderBy: {field: PUSHED_AT, direction: DESC}
    ) {
      nodes {
        name
        url
        visibility
        stargazerCount
        primaryLanguage {
          name
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 3) {
                edges {
                  node {
                    committedDate
                    messageHeadline
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

def get_repos():
    if MOCK_DATA:
        return [
            {
                "name": "mock-repo-1",
                "url": "https://github.com/LaTortu3/mock-repo-1",
                "visibility": "PUBLIC",
                "stargazerCount": 42,
                "primaryLanguage": {"name": "Python"},
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "edges": [
                                {"node": {"committedDate": "2026-05-24T00:00:00Z", "messageHeadline": "Initial commit"}},
                                {"node": {"committedDate": "2026-05-23T00:00:00Z", "messageHeadline": "Add features"}},
                            ]
                        }
                    }
                }
            },
            {
                "name": "mock-private-repo",
                "url": "https://github.com/LaTortu3/mock-private-repo",
                "visibility": "PRIVATE",
                "stargazerCount": 5,
                "primaryLanguage": {"name": "JavaScript"},
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "edges": [
                                {"node": {"committedDate": "2026-05-20T00:00:00Z", "messageHeadline": "Fix bug"}},
                            ]
                        }
                    }
                }
            }
        ]

    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post(GRAPHQL_URL, json={"query": QUERY}, headers=headers)
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    return data["data"]["viewer"]["repositories"]["nodes"]

def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def generate_markdown(repos):
    md = ""
    for i, repo in enumerate(repos, 1):
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        stars = repo.get("stargazerCount", 0)
        visibility = repo.get("visibility", "PUBLIC")
        lang = repo.get("primaryLanguage")
        lang_name = lang.get("name") if lang else "Unknown"

        md += f"{i}. **[{name}]({url})** (🌟 {stars} | 🔒 {visibility} | 💻 {lang_name})\n"

        branch = repo.get("defaultBranchRef")
        if branch and branch.get("target") and branch["target"].get("history"):
            commits = branch["target"]["history"].get("edges", [])
            if commits:
                md += "   - *Derniers commits :*\n"
                for commit_edge in commits:
                    commit = commit_edge.get("node", {})
                    date = format_date(commit.get("committedDate"))
                    msg = commit.get("messageHeadline", "Sans message")
                    md += f"     - [{date}] {msg}\n"
        md += "\n"
    return md

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # Use lambda to avoid backreference issues in replacement string
    new_readme = re.sub(
        pattern,
        lambda m: f"{m.group(1)}{new_content}\n{m.group(2)}",
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    try:
        repos = get_repos()
        markdown_content = generate_markdown(repos)
        update_readme(markdown_content)
        print("README.md updated successfully!")
    except Exception as e:
        print(f"Error updating README.md: {e}")
        exit(1)
