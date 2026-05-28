import os
import requests
import re

USERNAME = "LaTortu3"
TOKEN = os.getenv("GH_TOKEN")

# GraphQL query to fetch repositories and their last 3 commits
QUERY = """
query {
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
      nodes {
        name
        stargazerCount
        isPrivate
        primaryLanguage {
          name
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 3) {
                nodes {
                  messageHeadline
                  abbreviatedOid
                  pushedDate
                }
              }
            }
          }
        }
      }
    }
  }
}
""" % USERNAME

def fetch_repos():
    if not TOKEN:
        print("No GH_TOKEN found, using mock data for testing.")
        return [
            {
                "name": "mock-repo-1",
                "stargazerCount": 5,
                "isPrivate": False,
                "primaryLanguage": {"name": "Python"},
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "nodes": [
                                {"messageHeadline": "Initial commit", "abbreviatedOid": "a1b2c3d"}
                            ]
                        }
                    }
                }
            },
            {
                "name": "mock-repo-2",
                "stargazerCount": 10,
                "isPrivate": True,
                "primaryLanguage": {"name": "JavaScript"},
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "nodes": [
                                {"messageHeadline": "Fix bug", "abbreviatedOid": "e4f5g6h"},
                                {"messageHeadline": "Add feature", "abbreviatedOid": "i7j8k9l"}
                            ]
                        }
                    }
                }
            }
        ]

    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post("https://api.github.com/graphql", json={"query": QUERY}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("GraphQL Errors:", data["errors"])
            return []
        return data["data"]["user"]["repositories"]["nodes"]
    else:
        print(f"Query failed to run by returning code of {response.status_code}. {response.text}")
        return []

def format_repo(repo):
    name = repo["name"]
    stars = repo["stargazerCount"]
    visibility = "🔒 Private" if repo["isPrivate"] else "🌐 Public"
    lang = repo.get("primaryLanguage")
    lang_name = lang["name"] if lang else "N/A"

    output = f"#### 📁 [{name}](https://github.com/{USERNAME}/{name}) - {visibility}\n"
    output += f"**Langage:** {lang_name} | ⭐ **Stars:** {stars}\n\n"

    commits = []
    if repo.get("defaultBranchRef") and repo["defaultBranchRef"].get("target") and repo["defaultBranchRef"]["target"].get("history"):
        commits = repo["defaultBranchRef"]["target"]["history"]["nodes"]

    if commits:
        output += "**Derniers Commits:**\n"
        for commit in commits:
            msg = commit.get("messageHeadline", "N/A")
            oid = commit.get("abbreviatedOid", "N/A")
            output += f"- `[{oid}]` {msg}\n"
    else:
        output += "*- Aucun commit récent*\n"

    output += "\n"
    return output

def update_readme(repos_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    marker_start = "<!-- DYNAMIC_REPOS_START -->"
    marker_end = "<!-- DYNAMIC_REPOS_END -->"

    pattern = f"{marker_start}.*?{marker_end}"
    replacement = f"{marker_start}\n{repos_content}\n{marker_end}"

    new_readme = re.sub(pattern, replacement, readme, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    repos = fetch_repos()

    if repos:
        repos_content = ""
        for repo in repos:
            repos_content += format_repo(repo)

        update_readme(repos_content)
        print("README.md updated successfully!")
    else:
        print("No repositories found or error occurred.")
