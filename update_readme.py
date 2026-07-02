import os
import re
import sys
import requests
from datetime import datetime

# GraphQL Query to fetch repos, stars, language, and commits
QUERY = """
query {
  viewer {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
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
                nodes {
                  messageHeadline
                  committedDate
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

def fetch_repos():
    token = os.environ.get("GH_TOKEN")
    is_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_actions:
            print("Error: GH_TOKEN is not set in GitHub Actions environment.")
            sys.exit(1)
        else:
            print("Warning: GH_TOKEN not found. Using mock data for local testing.")
            return [
                {
                    "name": "Mock-Repo-1",
                    "url": "https://github.com/mock/repo1",
                    "visibility": "PUBLIC",
                    "stargazerCount": 42,
                    "primaryLanguage": {"name": "Python"},
                    "defaultBranchRef": {
                        "target": {
                            "history": {
                                "nodes": [
                                    {"messageHeadline": "Initial commit", "committedDate": "2023-10-01T12:00:00Z"},
                                    {"messageHeadline": "Update docs", "committedDate": "2023-10-02T12:00:00Z"}
                                ]
                            }
                        }
                    }
                }
            ]

    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"bearer {token}"}
    response = requests.post(url, json={"query": QUERY}, headers=headers)

    if response.status_code != 200:
        print(f"Error fetching data: {response.status_code} - {response.text}")
        sys.exit(1)

    data = response.json()
    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        sys.exit(1)

    return data["data"]["viewer"]["repositories"]["nodes"]

def generate_markdown(repos):
    md = ""
    for repo in repos:
        name = repo.get("name")
        url = repo.get("url")
        stars = repo.get("stargazerCount", 0)
        lang_data = repo.get("primaryLanguage")
        lang = lang_data.get("name") if lang_data else "N/A"

        md += f"### [{name}]({url}) 🌟 {stars} | 🛠 {lang}\n\n"
        md += "**Derniers Commits :**\n"

        branch = repo.get("defaultBranchRef")
        if branch and branch.get("target"):
            commits = branch["target"].get("history", {}).get("nodes", [])
            for commit in commits:
                msg = commit.get("messageHeadline")
                date_str = commit.get("committedDate")
                # Parse ISO date string
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                formatted_date = date_obj.strftime("%d/%m/%Y")
                md += f"- `{formatted_date}` : {msg}\n"
        else:
            md += "- Aucun commit récent trouvé.\n"
        md += "\n"
    return md

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # Use lambda to avoid regex replacement issues with escaped characters
    updated_content = re.sub(
        pattern,
        lambda m: f"{m.group(1)}{new_content}{m.group(2)}",
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_content)

if __name__ == "__main__":
    repos = fetch_repos()
    print(f"Fetched {len(repos)} repositories.")
    new_md = generate_markdown(repos)
    update_readme(new_md)
    print("README.md updated successfully.")