import os
import requests
import re
from datetime import datetime

# Configuration
GITHUB_GRAPHQL_URL = "https://api.github.com/graphql"
GH_TOKEN = os.getenv("GH_TOKEN")
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

MOCK_DATA = """
#### 🌟 [Test-Repo](https://github.com/LaTortu3/Test-Repo)
> 👁️ **Public** | ⭐ 42 | 🛠️ Python

**Dernières avancées de code :**
- `2023-10-27` : ✨ Initial commit
- `2023-10-28` : 🐛 Fix bug in main.py
- `2023-10-29` : 🚀 Add new feature

---
"""

def fetch_repos():
    if not GH_TOKEN:
        if IS_GITHUB_ACTIONS:
            raise ValueError("GH_TOKEN is missing in GitHub Actions environment. Mock data injection prevented.")
        print("Warning: GH_TOKEN missing, using mock data for local testing.")
        return MOCK_DATA

    headers = {
        "Authorization": f"Bearer {GH_TOKEN}",
        "Content-Type": "application/json",
    }

    query = """
    {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, isFork: false) {
          nodes {
            name
            url
            isPrivate
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

    try:
        response = requests.post(GITHUB_GRAPHQL_URL, json={"query": query}, headers=headers)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from GitHub: {e}")
        return ""

    repos = data.get("data", {}).get("viewer", {}).get("repositories", {}).get("nodes", [])

    markdown_content = ""
    for repo in repos:
        name = repo.get("name")
        url = repo.get("url")
        visibility = "Privé" if repo.get("isPrivate") else "Public"
        stars = repo.get("stargazerCount", 0)

        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name") if lang_node else "Non défini"

        markdown_content += f"\n#### 🌟 [{name}]({url})\n"
        markdown_content += f"> 👁️ **{visibility}** | ⭐ {stars} | 🛠️ {lang}\n\n"
        markdown_content += "**Dernières avancées de code :**\n"

        branch_ref = repo.get("defaultBranchRef")
        if branch_ref and branch_ref.get("target"):
            commits = branch_ref["target"].get("history", {}).get("nodes", [])
            for commit in commits:
                msg = commit.get("messageHeadline", "Commit sans message")
                date_str = commit.get("committedDate", "")
                if date_str:
                    try:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                        date_formatted = date_obj.strftime("%Y-%m-%d")
                    except ValueError:
                        date_formatted = date_str
                else:
                    date_formatted = "Inconnue"
                markdown_content += f"- `{date_formatted}` : {msg}\n"
        else:
             markdown_content += "- *Aucun commit récent trouvé.*\n"

        markdown_content += "\n---\n"

    return markdown_content

def update_readme(content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # We use a lambda to avoid issues with backreferences in `content` if it contains \1, \2 etc
    updated_readme = re.sub(
        pattern,
        lambda m: f"{m.group(1)}{content}{m.group(2)}",
        readme,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print("README.md updated successfully!")

if __name__ == "__main__":
    new_content = fetch_repos()
    if new_content:
        update_readme(new_content)
    else:
        print("No content generated. README.md was not updated.")
