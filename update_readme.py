import os
import re
import requests
from datetime import datetime

# Define GraphQL endpoint and query
GRAPHQL_URL = "https://api.github.com/graphql"

GRAPHQL_QUERY = """
query {
  viewer {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
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

def get_repos():
    token = os.getenv("GH_TOKEN")
    is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise ValueError("GH_TOKEN is missing in the GitHub Actions environment.")
        print("GH_TOKEN is missing. Falling back to mock data.")
        return get_mock_data()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(GRAPHQL_URL, json={"query": GRAPHQL_QUERY}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def get_mock_data():
    return {
        "data": {
            "viewer": {
                "repositories": {
                    "nodes": [
                        {
                            "name": "Awesome-Python-Script",
                            "url": "https://github.com/LaTortu3/Awesome-Python-Script",
                            "isPrivate": False,
                            "stargazerCount": 42,
                            "primaryLanguage": {"name": "Python"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Add new feature", "committedDate": "2023-10-27T10:00:00Z"},
                                            {"messageHeadline": "Fix bug", "committedDate": "2023-10-26T14:30:00Z"},
                                            {"messageHeadline": "Initial commit", "committedDate": "2023-10-25T09:15:00Z"}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "name": "Secret-Project-X",
                            "url": "https://github.com/LaTortu3/Secret-Project-X",
                            "isPrivate": True,
                            "stargazerCount": 0,
                            "primaryLanguage": {"name": "C++"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Update engine config", "committedDate": "2023-10-20T16:45:00Z"}
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        }
    }

def format_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%Y-%m-%d %H:%M")

def generate_markdown(data):
    if not data or not data.get("data") or not data["data"].get("viewer") or not data["data"]["viewer"].get("repositories"):
        return "<p>Aucun dépôt trouvé.</p>"

    repos = data["data"]["viewer"]["repositories"]["nodes"]

    if not repos:
        return "<p>Aucun dépôt trouvé.</p>"

    md_content = ""
    for repo in repos:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        is_private = "🔒 Privé" if repo.get("isPrivate") else "🌐 Public"
        stars = repo.get("stargazerCount", 0)

        lang = "Unknown"
        if repo.get("primaryLanguage"):
            lang = repo["primaryLanguage"].get("name", "Unknown")

        md_content += f"#### [{name}]({url}) | {is_private} | ⭐ {stars} | 🔵 {lang}\n"

        commits = []
        if repo.get("defaultBranchRef") and repo["defaultBranchRef"].get("target") and repo["defaultBranchRef"]["target"].get("history"):
            commits = repo["defaultBranchRef"]["target"]["history"].get("nodes", [])

        if commits:
            md_content += "- **Derniers commits :**\n"
            for commit in commits:
                msg = commit.get("messageHeadline", "Sans message")
                date = format_date(commit.get("committedDate"))
                md_content += f"  - `{date}` : {msg}\n"
        else:
             md_content += "- *Aucun commit récent trouvé.*\n"

        md_content += "\n"

    return md_content

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    pattern = r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)'

    # Use lambda to prevent backreference errors
    updated_content = re.sub(
        pattern,
        lambda m: f'{m.group(1)}{new_content}{m.group(2)}',
        readme_content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("README.md updated successfully!")

if __name__ == "__main__":
    print("Fetching repository data...")
    data = get_repos()
    print("Generating markdown...")
    markdown_content = generate_markdown(data)
    print("Updating README.md...")
    update_readme(markdown_content)
