import os
import requests
import json
import re

def get_mock_data():
    return [
        {
            "name": "MockRepo-GameEngine",
            "url": "https://github.com/LaTortu3/MockRepo-GameEngine",
            "isPrivate": False,
            "stargazerCount": 42,
            "primaryLanguage": {"name": "C++"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Implement physics engine", "committedDate": "2024-05-10T12:00:00Z"}},
                            {"node": {"messageHeadline": "Fix memory leak", "committedDate": "2024-05-09T15:30:00Z"}},
                            {"node": {"messageHeadline": "Initial commit", "committedDate": "2024-05-01T08:00:00Z"}}
                        ]
                    }
                }
            }
        },
        {
            "name": "MockRepo-AutomationScripts",
            "url": "https://github.com/LaTortu3/MockRepo-AutomationScripts",
            "isPrivate": True,
            "stargazerCount": 0,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Add GraphQL fetch script", "committedDate": "2024-05-11T10:00:00Z"}},
                            {"node": {"messageHeadline": "Setup CI/CD workflow", "committedDate": "2024-05-11T09:00:00Z"}}
                        ]
                    }
                }
            }
        }
    ]

def fetch_repos_graphql(token):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    query = """
    query {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, affiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
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
                    edges {
                      node {
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
    }
    """

    response = requests.post(url, json={"query": query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        return data["data"]["viewer"]["repositories"]["nodes"]
    else:
        raise Exception(f"Query failed with status code {response.status_code}: {response.text}")

def format_repos(repos_data):
    formatted_content = ""
    for repo in repos_data:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        visibility = "🔒 Privé" if repo.get("isPrivate") else "🌐 Public"
        stars = repo.get("stargazerCount", 0)

        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name") if lang_node else "N/A"

        formatted_content += f"#### [{name}]({url}) - {visibility}\n"
        formatted_content += f"**Langage Principal:** {lang} | **Étoiles:** ⭐ {stars}\n\n"

        default_branch = repo.get("defaultBranchRef") or {}
        commits_history = default_branch.get("target", {}).get("history", {}).get("edges", [])
        if commits_history:
            formatted_content += "**Derniers Commits:**\n"
            for edge in commits_history:
                commit = edge.get("node", {})
                message = commit.get("messageHeadline", "No message")
                date_str = commit.get("committedDate", "")[:10]  # Just take the YYYY-MM-DD part
                formatted_content += f"- `{date_str}`: {message}\n"
        else:
            formatted_content += "*Aucun commit récent ou branche par défaut introuvable.*\n"

        formatted_content += "\n---\n\n"

    return formatted_content

def update_readme(new_content):
    readme_path = "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        start_marker = "<!-- DYNAMIC_REPOS_START -->"
        end_marker = "<!-- DYNAMIC_REPOS_END -->"

        pattern = re.compile(rf"{start_marker}.*?{end_marker}", re.DOTALL)

        if not pattern.search(content):
            print("Markers not found in README.md")
            return

        new_readme_content = pattern.sub(f"{start_marker}\n{new_content}{end_marker}", content)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme_content)

        print("README.md successfully updated!")
    except Exception as e:
        print(f"Error updating README.md: {e}")

if __name__ == "__main__":
    token = os.environ.get("GH_TOKEN")
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise ValueError("GH_TOKEN is missing in GitHub Actions environment. Aborting to prevent mock data injection.")
        print("GH_TOKEN not found. Running locally with mock data.")
        repos_data = get_mock_data()
    else:
        print("GH_TOKEN found. Fetching data from GitHub GraphQL API.")
        repos_data = fetch_repos_graphql(token)

    print(f"Fetched {len(repos_data)} repositories.")
    formatted_repos = format_repos(repos_data)
    update_readme(formatted_repos)
