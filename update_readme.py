import os
import requests
import re
from datetime import datetime

# The GitHub GraphQL API endpoint
API_URL = 'https://api.github.com/graphql'

# The GraphQL query to fetch repositories and their latest commits
QUERY = """
{
  viewer {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        isPrivate
        stargazerCount
        primaryLanguage {
          name
        }
        url
        description
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

def get_repos_data(token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(API_URL, json={'query': QUERY}, headers=headers)
    response.raise_for_status()
    return response.json()

def generate_mock_data():
    print("WARNING: Using mock data because GH_TOKEN is missing locally.")
    return {
        "data": {
            "viewer": {
                "repositories": {
                    "nodes": [
                        {
                            "name": "mock-repo-1",
                            "isPrivate": False,
                            "stargazerCount": 42,
                            "primaryLanguage": {"name": "Python"},
                            "url": "https://github.com/mock/mock-repo-1",
                            "description": "A mock repository for testing.",
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T10:00:00Z", "oid": "abc1234"},
                                            {"messageHeadline": "Add feature X", "committedDate": "2023-10-26T15:30:00Z", "oid": "def5678"}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "name": "secret-project",
                            "isPrivate": True,
                            "stargazerCount": 0,
                            "primaryLanguage": {"name": "C++"},
                            "url": "https://github.com/mock/secret-project",
                            "description": "Top secret stuff.",
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Fix critical bug", "committedDate": "2023-10-25T09:15:00Z", "oid": "ghi9012"}
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
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def create_markdown_for_repos(repos):
    md = ""
    for repo in repos:
        name = repo.get('name', 'Unknown')
        url = repo.get('url', '#')
        is_private = repo.get('isPrivate', False)
        visibility = "🔒 Privé" if is_private else "🌐 Public"
        stars = repo.get('stargazerCount', 0)
        lang_node = repo.get('primaryLanguage')
        lang = lang_node.get('name') if lang_node else "N/A"
        desc = repo.get('description') or "Aucune description."

        md += f"#### [{name}]({url})\n"
        md += f"**Visibilité:** {visibility} | **⭐ Étoiles:** {stars} | **Langage Principal:** {lang}\n\n"
        md += f"*{desc}*\n\n"

        md += "**Derniers Commits :**\n"

        commits = []
        try:
            commits = repo['defaultBranchRef']['target']['history']['nodes']
        except (KeyError, TypeError):
            pass

        if commits:
            for commit in commits:
                msg = commit.get('messageHeadline', 'Sans message')
                date = format_date(commit.get('committedDate', ''))
                sha = commit.get('oid', '')[:7]
                md += f"- `{sha}` : {msg} *(le {date})*\n"
        else:
            md += "- *Aucun commit récent trouvé.*\n"

        md += "\n---\n\n"

    return md

def update_readme(new_content):
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()

    # The markers to look for
    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    pattern = re.compile(rf"{start_marker}.*?{end_marker}", re.DOTALL)

    replacement = f"{start_marker}\n{new_content}\n{end_marker}"

    new_readme = re.sub(pattern, replacement, readme)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_readme)

    print("README.md has been successfully updated!")

def main():
    token = os.environ.get('GH_TOKEN')
    is_actions = os.environ.get('GITHUB_ACTIONS') == 'true'

    if not token:
        if is_actions:
            raise ValueError("GH_TOKEN is missing in the GitHub Actions environment. Aborting to prevent mock data injection.")
        else:
            data = generate_mock_data()
    else:
        print("Fetching data from GitHub...")
        data = get_repos_data(token)

    try:
        repos = data['data']['viewer']['repositories']['nodes']
    except KeyError:
        print("Unexpected data format received from API.")
        return

    print(f"Found {len(repos)} repositories. Formatting data...")
    md_content = create_markdown_for_repos(repos)

    update_readme(md_content)

if __name__ == "__main__":
    main()
