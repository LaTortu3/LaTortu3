import os
import requests
import re

# GraphQL query to get the authenticated user's repositories
GRAPHQL_QUERY = """
{
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

def get_repos_data(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post('https://api.github.com/graphql', json={'query': GRAPHQL_QUERY}, headers=headers)
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
                            "name": "SuperGameEngine",
                            "url": "https://github.com/LaTortu3/SuperGameEngine",
                            "isPrivate": False,
                            "stargazerCount": 42,
                            "primaryLanguage": {"name": "C++"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Add Lua scripting support"},
                                            {"messageHeadline": "Fix rendering bug"},
                                            {"messageHeadline": "Initial commit"}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "name": "SecretProjectX",
                            "url": "https://github.com/LaTortu3/SecretProjectX",
                            "isPrivate": True,
                            "stargazerCount": 5,
                            "primaryLanguage": {"name": "Python"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Update AI models"},
                                            {"messageHeadline": "Refactor data pipeline"}
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

def generate_markdown(data):
    nodes = data.get("data", {}).get("viewer", {}).get("repositories", {}).get("nodes", [])
    if not nodes:
         return "Aucun dépôt trouvé.\n"

    markdown = ""
    for repo in nodes:
        name = repo.get("name")
        url = repo.get("url")
        is_private = repo.get("isPrivate")
        stars = repo.get("stargazerCount")

        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name") if lang_node else "N/A"

        visibility = "🔒 Privé" if is_private else "🌍 Public"

        markdown += f"#### [{name}]({url}) - {visibility}\n"
        markdown += f"**Langage Principal:** {lang} | ⭐ **Stars:** {stars}\n\n"

        commits = []
        default_branch = repo.get("defaultBranchRef")
        if default_branch:
            target = default_branch.get("target")
            if target:
                history = target.get("history")
                if history:
                    commits = history.get("nodes", [])

        if commits:
            markdown += "**Derniers Commits:**\n"
            for commit in commits:
                markdown += f"- {commit.get('messageHeadline')}\n"
        else:
            markdown += "*Aucun commit trouvé.*\n"

        markdown += "\n"

    return markdown

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    pattern = re.compile(f"{start_marker}.*?{end_marker}", re.DOTALL)

    replacement = f"{start_marker}\n{new_content}\n{end_marker}"

    new_readme = re.sub(pattern, replacement, readme)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    token = os.getenv("GH_TOKEN")
    is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"

    if token:
        print("Fetching data from GitHub API...")
        data = get_repos_data(token)
    else:
        if is_github_actions:
            raise ValueError("GH_TOKEN is missing in GitHub Actions environment. Mock data injection prevented.")
        else:
            print("GH_TOKEN not found. Using mock data for local testing...")
            data = get_mock_data()

    markdown_content = generate_markdown(data)
    update_readme(markdown_content)
    print("README.md updated successfully!")
