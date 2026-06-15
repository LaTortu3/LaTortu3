import os
import requests
import json
import datetime

# GitHub GraphQL API Endpoint
GITHUB_GRAPHQL_URL = 'https://api.github.com/graphql'

# The GraphQL Query
GRAPHQL_QUERY = """
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

def fetch_github_data(token):
    """Fetches repository data from GitHub using the GraphQL API."""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(GITHUB_GRAPHQL_URL, json={'query': GRAPHQL_QUERY}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch data from GitHub API: {response.status_code} - {response.text}")

def get_mock_data():
    """Returns mock data for local testing without a token."""
    return {
        "data": {
            "viewer": {
                "repositories": {
                    "nodes": [
                        {
                            "name": "Mock-Repo-1",
                            "url": "https://github.com/mock/mock-repo-1",
                            "isPrivate": False,
                            "stargazerCount": 42,
                            "primaryLanguage": {"name": "Python"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "edges": [
                                            {"node": {"messageHeadline": "Update README", "committedDate": "2024-05-15T10:00:00Z"}},
                                            {"node": {"messageHeadline": "Fix typo", "committedDate": "2024-05-14T09:00:00Z"}},
                                            {"node": {"messageHeadline": "Initial commit", "committedDate": "2024-05-13T08:00:00Z"}}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "name": "Secret-Project-X",
                            "url": "https://github.com/mock/secret-project",
                            "isPrivate": True,
                            "stargazerCount": 0,
                            "primaryLanguage": {"name": "C++"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "edges": [
                                            {"node": {"messageHeadline": "Implement feature Y", "committedDate": "2024-05-10T12:00:00Z"}}
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
    """Formats an ISO 8601 date string to a shorter format."""
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return str(date_str)

def generate_markdown(data):
    """Generates the Markdown string from the GitHub data."""
    repos = data.get('data', {}).get('viewer', {}).get('repositories', {}).get('nodes', [])

    if not repos:
        return "Aucun dépôt trouvé.\n"

    md_lines = []
    for repo in repos:
        name = repo.get('name', 'Unknown')
        url = repo.get('url', '#')
        is_private = repo.get('isPrivate', False)
        stars = repo.get('stargazerCount', 0)

        lang_node = repo.get('primaryLanguage')
        lang = lang_node.get('name') if lang_node else 'N/A'

        visibility_badge = "🔒 Privé" if is_private else "🌍 Public"
        star_badge = f"⭐ {stars}"

        md_lines.append(f"#### 📦 [{name}]({url})")
        md_lines.append(f"**{visibility_badge}** | **{star_badge}** | 🔤 **{lang}**")
        md_lines.append("")

        # Commits
        commits_node = repo.get('defaultBranchRef')
        if commits_node and commits_node.get('target') and commits_node['target'].get('history'):
            edges = commits_node['target']['history'].get('edges', [])
            if edges:
                md_lines.append("📝 **Derniers commits :**")
                for edge in edges:
                    commit = edge.get('node', {})
                    msg = commit.get('messageHeadline', 'No message')
                    date = format_date(commit.get('committedDate', ''))
                    md_lines.append(f"- `{date}` : {msg}")
            else:
                md_lines.append("_Aucun commit trouvé._")
        else:
            md_lines.append("_Historique des commits indisponible._")

        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    return "\n".join(md_lines)

def update_readme(markdown_content):
    """Updates the README.md file between the dynamic markers."""
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()

    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    start_idx = readme.find(start_marker)
    end_idx = readme.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        print("Error: Could not find dynamic markers in README.md")
        return

    # Keep exactly the markers and replace everything in between
    new_readme = (
        readme[:start_idx + len(start_marker)] + "\n" +
        markdown_content + "\n" +
        readme[end_idx:]
    )

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_readme)

    print("README.md successfully updated!")

if __name__ == '__main__':
    github_token = os.environ.get('GH_TOKEN')
    is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'

    if not github_token:
        if is_github_actions:
            raise Exception("GH_TOKEN is missing in the GitHub Actions environment. Cannot proceed.")
        else:
            print("GH_TOKEN not found. Falling back to mock data for local testing.")
            data = get_mock_data()
    else:
        print("GH_TOKEN found. Fetching real data from GitHub.")
        data = fetch_github_data(github_token)

    markdown = generate_markdown(data)
    update_readme(markdown)
