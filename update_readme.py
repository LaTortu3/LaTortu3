import os
import requests
import re

def fetch_repos():
    token = os.environ.get("GH_TOKEN")

    if not token:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            raise ValueError("GH_TOKEN environment variable is missing in GitHub Actions!")
        print("GH_TOKEN not found. Using mock data for local testing.")
        return get_mock_data()

    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }

    query = """
    {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
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

    response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

    result = response.json()
    if 'errors' in result:
        raise Exception(f"GraphQL errors: {result['errors']}")

    return result['data']['viewer']['repositories']['nodes']

def get_mock_data():
    return [
        {
            "name": "mock-repo-1",
            "url": "https://github.com/LaTortu3/mock-repo-1",
            "visibility": "PUBLIC",
            "stargazerCount": 42,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T10:00:00Z"}},
                            {"node": {"messageHeadline": "Update README", "committedDate": "2023-10-28T12:00:00Z"}}
                        ]
                    }
                }
            }
        },
        {
             "name": "mock-private-project",
            "url": "https://github.com/LaTortu3/mock-private-project",
            "visibility": "PRIVATE",
            "stargazerCount": 0,
            "primaryLanguage": {"name": "JavaScript"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Add new feature", "committedDate": "2023-10-29T15:30:00Z"}}
                        ]
                    }
                }
            }
        }
    ]

def generate_markdown(repos):
    md = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        visibility = repo['visibility'].capitalize()
        stars = repo['stargazerCount']
        lang = repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else "N/A"

        md += f"#### [{name}]({url}) - {visibility} 🔒\n" if visibility == "Private" else f"#### [{name}]({url})\n"
        md += f"- **Language:** {lang} | **Stars:** {stars} ⭐\n"

        commits = []
        if repo.get('defaultBranchRef') and repo['defaultBranchRef'].get('target') and repo['defaultBranchRef']['target'].get('history'):
             commits = repo['defaultBranchRef']['target']['history']['edges']

        if commits:
            md += "- **Derniers Commits:**\n"
            for edge in commits:
                commit = edge['node']
                msg = commit['messageHeadline']
                date = commit['committedDate'][:10]
                md += f"  - `{date}` : {msg}\n"
        md += "\n"
    return md

def update_readme(new_content):
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)'
    replacement = lambda m: f"{m.group(1)}{new_content}{m.group(2)}"

    updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(updated_content)

if __name__ == "__main__":
    repos = fetch_repos()
    md_content = generate_markdown(repos)
    update_readme(md_content)
    print("README.md updated successfully!")
