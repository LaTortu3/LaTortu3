import os
import requests
import json

# Configuration
USERNAME = "LaTortu3"
README_PATH = "README.md"
START_MARKER = "<!-- DYNAMIC_REPOS_START -->"
END_MARKER = "<!-- DYNAMIC_REPOS_END -->"

def fetch_repos_graphql(token):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    query = """
    query {
      user(login: "%s") {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            isPrivate
            stargazerCount
            primaryLanguage {
              name
            }
            url
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
    """ % USERNAME

    response = requests.post(url, json={'query': query}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        print(response.text)
        return None

def get_mock_data():
    return {
        "data": {
            "user": {
                "repositories": {
                    "nodes": [
                        {
                            "name": "mock-repo-1",
                            "isPrivate": False,
                            "stargazerCount": 42,
                            "primaryLanguage": {"name": "Python"},
                            "url": "https://github.com/LaTortu3/mock-repo-1",
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T10:00:00Z"},
                                            {"messageHeadline": "Update README", "committedDate": "2023-10-28T10:00:00Z"},
                                            {"messageHeadline": "Fix bug", "committedDate": "2023-10-29T10:00:00Z"}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "name": "mock-private-repo",
                            "isPrivate": True,
                            "stargazerCount": 0,
                            "primaryLanguage": {"name": "C++"},
                            "url": "https://github.com/LaTortu3/mock-private-repo",
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "WIP: New Feature", "committedDate": "2023-11-01T12:00:00Z"}
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

def format_repo_md(repo):
    name = repo['name']
    url = repo['url']
    visibility = "🔒 Private" if repo.get('isPrivate') else "🌐 Public"
    stars = repo.get('stargazerCount', 0)

    lang = repo.get('primaryLanguage')
    lang_name = lang['name'] if lang else "N/A"

    md = f"#### [{name}]({url}) • {visibility} • ⭐ {stars} • 💻 {lang_name}\n"

    branch_ref = repo.get('defaultBranchRef')
    if branch_ref and branch_ref.get('target') and branch_ref['target'].get('history'):
        commits = branch_ref['target']['history']['nodes']
        if commits:
            md += "  **Recent Commits:**\n"
            for commit in commits:
                msg = commit['messageHeadline']
                date = commit['committedDate'][:10]
                md += f"  - `{date}`: {msg}\n"
        else:
             md += "  - _No recent commits found._\n"
    else:
        md += "  - _No commit history available._\n"

    return md

def update_readme(new_content):
    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    start_idx = content.find(START_MARKER)
    end_idx = content.find(END_MARKER)

    if start_idx != -1 and end_idx != -1:
        updated_content = content[:start_idx + len(START_MARKER)] + "\n" + new_content + content[end_idx:]
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("README.md updated successfully.")
    else:
        print("Markers not found in README.md")

def main():
    token = os.environ.get('GH_TOKEN')

    if token:
        print("GH_TOKEN found, querying GitHub API...")
        data = fetch_repos_graphql(token)
    else:
        print("GH_TOKEN not found, using mock data for testing...")
        data = get_mock_data()

    if not data or 'data' not in data or 'user' not in data['data'] or not data['data']['user']:
        print("Error: Invalid data format or failed to fetch data.")
        return

    repos = data['data']['user']['repositories']['nodes']

    markdown_content = ""
    for repo in repos:
        markdown_content += format_repo_md(repo) + "\n"

    update_readme(markdown_content)

if __name__ == "__main__":
    main()
