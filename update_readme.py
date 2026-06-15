import os
import sys
import json
import requests

def fetch_repositories(token):
    url = 'https://api.github.com/graphql'
    headers = {
        'Authorization': f'bearer {token}',
        'Content-Type': 'application/json'
    }

    query = """
    {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: [OWNER]) {
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
                      oid
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

    response = requests.post(url, headers=headers, json={'query': query})
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def format_repo_data(data):
    if not data or 'data' not in data or 'viewer' not in data['data']:
        return "<!-- Impossible de charger les dépôts pour le moment -->"

    repos = data['data']['viewer']['repositories']['nodes']
    markdown = ""

    for repo in repos:
        name = repo.get('name', 'Unnamed')
        url = repo.get('url', '#')
        visibility = repo.get('visibility', 'Public')
        stars = repo.get('stargazerCount', 0)

        lang_node = repo.get('primaryLanguage')
        lang = lang_node.get('name') if lang_node else 'N/A'

        badge_vis = "🔒 Privé" if visibility == "PRIVATE" else "🌍 Public"
        markdown += f"#### 📁 [{name}]({url}) | {badge_vis} | ⭐ {stars} | 🛠 {lang}\n"

        # Commits
        branch_ref = repo.get('defaultBranchRef')
        if branch_ref and branch_ref.get('target') and branch_ref['target'].get('history'):
            commits = branch_ref['target']['history']['nodes']
            if commits:
                markdown += "  **Derniers commits :**\n"
                for commit in commits:
                    msg = commit.get('messageHeadline', '')
                    date = commit.get('committedDate', '')[:10]
                    oid = commit.get('oid', '')[:7]
                    markdown += f"  - `{oid}` ({date}) : {msg}\n"
            else:
                markdown += "  *Aucun commit récent.*\n"
        else:
             markdown += "  *Historique non disponible.*\n"
        markdown += "\n"

    return markdown

def get_mock_data():
    return {
        "data": {
            "viewer": {
                "repositories": {
                    "nodes": [
                        {
                            "name": "Mock-Project-Alpha",
                            "url": "https://github.com/mock/alpha",
                            "visibility": "PUBLIC",
                            "stargazerCount": 42,
                            "primaryLanguage": {"name": "Python"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T10:00:00Z", "oid": "a1b2c3d"}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "name": "Secret-Lua-Engine",
                            "url": "https://github.com/mock/secret",
                            "visibility": "PRIVATE",
                            "stargazerCount": 5,
                            "primaryLanguage": {"name": "Lua"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Optimize memory allocation", "committedDate": "2023-10-26T15:30:00Z", "oid": "f9e8d7c"}
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

def update_readme(new_content):
    with open('README.md', 'r', encoding='utf-8') as file:
        readme = file.read()

    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    start_idx = readme.find(start_marker)
    end_idx = readme.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise Exception("Could not find dynamic markers in README.md")

    updated_readme = (
        readme[:start_idx + len(start_marker)] +
        "\n" + new_content + "\n" +
        readme[end_idx:]
    )

    with open('README.md', 'w', encoding='utf-8') as file:
        file.write(updated_readme)

if __name__ == "__main__":
    token = os.environ.get('GH_TOKEN')
    is_actions = os.environ.get('GITHUB_ACTIONS') == 'true'

    if not token:
        if is_actions:
            raise Exception("GH_TOKEN is missing in the GitHub Actions environment.")
        else:
            print("Running locally without GH_TOKEN. Using mock data.")
            data = get_mock_data()
    else:
        print("GH_TOKEN found. Fetching data from GitHub...")
        data = fetch_repositories(token)

    formatted_markdown = format_repo_data(data)
    update_readme(formatted_markdown)
    print("README.md has been successfully updated.")
