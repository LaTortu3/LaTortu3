import os
import requests
import re

GITHUB_TOKEN = os.getenv('GH_TOKEN')
USERNAME = 'LaTortu3'

GRAPHQL_QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
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
""" % USERNAME

def fetch_repos():
    if not GITHUB_TOKEN:
        print("Warning: GH_TOKEN not found. Falling back to mock data.")
        return [
            {
                "name": "mock-repo-1",
                "isPrivate": False,
                "stargazerCount": 5,
                "primaryLanguage": {"name": "Python"},
                "url": "https://github.com/LaTortu3/mock-repo-1",
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "nodes": [
                                {"messageHeadline": "Initial commit", "committedDate": "2023-01-01T00:00:00Z", "oid": "1234567890abcdef"},
                                {"messageHeadline": "Update README", "committedDate": "2023-01-02T00:00:00Z", "oid": "abcdef1234567890"}
                            ]
                        }
                    }
                }
            },
            {
                "name": "mock-private-repo",
                "isPrivate": True,
                "stargazerCount": 2,
                "primaryLanguage": {"name": "JavaScript"},
                "url": "https://github.com/LaTortu3/mock-private-repo",
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "nodes": [
                                {"messageHeadline": "Fix bug", "committedDate": "2023-01-03T00:00:00Z", "oid": "0987654321fedcba"}
                            ]
                        }
                    }
                }
            }
        ]

    headers = {
        "Authorization": f"bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            'https://api.github.com/graphql',
            json={'query': GRAPHQL_QUERY},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            print(f"GraphQL Errors: {data['errors']}")
            return []

        return data.get('data', {}).get('user', {}).get('repositories', {}).get('nodes', [])
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def format_repo_md(repo):
    name = repo.get('name', 'Unknown')
    url = repo.get('url', '#')
    is_private = repo.get('isPrivate', False)
    stars = repo.get('stargazerCount', 0)
    lang_info = repo.get('primaryLanguage')
    lang = lang_info.get('name', 'N/A') if lang_info else 'N/A'

    visibility = "🔒 Private" if is_private else "🌍 Public"

    md = f"#### [{name}]({url}) - {visibility}\n"
    md += f"- **⭐ Stars:** {stars} | **🔤 Language:** {lang}\n"

    commits = []
    default_branch = repo.get('defaultBranchRef')
    if default_branch:
        target = default_branch.get('target')
        if target:
            history = target.get('history')
            if history:
                commits = history.get('nodes', [])

    if commits:
        md += "- **Derniers Commits:**\n"
        for commit in commits:
            msg = commit.get('messageHeadline', 'No message')
            date = commit.get('committedDate', '').split('T')[0]
            oid = commit.get('oid', '')[:7]
            md += f"  - `{oid}` ({date}): {msg}\n"
    else:
        md += "- *Aucun commit récent*\n"

    return md + "\n"

def update_readme(repos):
    readme_path = 'README.md'

    if not os.path.exists(readme_path):
        print(f"{readme_path} not found!")
        return

    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()

    start_marker = r'<!-- DYNAMIC_REPOS_START -->'
    end_marker = r'<!-- DYNAMIC_REPOS_END -->'

    pattern = re.compile(f'({start_marker}).*?({end_marker})', re.DOTALL)

    if not pattern.search(content):
        print("Markers not found in README.md")
        return

    repos_md = "\n".join([format_repo_md(repo) for repo in repos])

    new_content = pattern.sub(f'\\1\n{repos_md}\\2', content)

    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("README.md updated successfully!")

if __name__ == "__main__":
    print("Fetching repos...")
    repos = fetch_repos()
    if repos:
        print(f"Found {len(repos)} repos. Updating README...")
        update_readme(repos)
    else:
        print("No repos found to update.")
