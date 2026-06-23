import os
import re
import requests

def get_repositories(token):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}"}
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
    response = requests.post(url, json={'query': query}, headers=headers)
    response.raise_for_status()
    return response.json()['data']['viewer']['repositories']['nodes']

def generate_markdown(repos):
    markdown = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        visibility = "🔒 Privé" if repo['isPrivate'] else "🌐 Public"
        stars = repo['stargazerCount']
        lang = repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else "N/A"

        markdown += f"#### [{name}]({url})\n"
        markdown += f"**Visibilité:** {visibility} | **Stars:** ⭐ {stars} | **Langage:** {lang}\n\n"

        commits = []
        if repo.get('defaultBranchRef') and repo['defaultBranchRef'].get('target') and repo['defaultBranchRef']['target'].get('history'):
            edges = repo['defaultBranchRef']['target']['history']['edges']
            for edge in edges:
                commits.append(edge['node']['messageHeadline'])

        if commits:
            markdown += "**Derniers Commits:**\n"
            for commit in commits:
                markdown += f"- {commit}\n"
        else:
            markdown += "*Aucun commit récent*\n"

        markdown += "\n---\n\n"

    return markdown

def main():
    token = os.environ.get("GH_TOKEN")

    if not token:
        if os.environ.get("GITHUB_ACTIONS"):
            raise ValueError("GH_TOKEN is missing in GitHub Actions environment.")
        else:
            print("GH_TOKEN missing. Using mock data for local testing.")
            repos = [
                {
                    'name': 'mock-repo-1',
                    'url': 'https://github.com/LaTortu3/mock-repo-1',
                    'isPrivate': False,
                    'stargazerCount': 42,
                    'primaryLanguage': {'name': 'Python'},
                    'defaultBranchRef': {
                        'target': {
                            'history': {
                                'edges': [
                                    {'node': {'messageHeadline': 'Initial commit', 'committedDate': '2023-01-01T00:00:00Z'}},
                                    {'node': {'messageHeadline': 'Update README', 'committedDate': '2023-01-02T00:00:00Z'}}
                                ]
                            }
                        }
                    }
                },
                {
                    'name': 'secret-project',
                    'url': 'https://github.com/LaTortu3/secret-project',
                    'isPrivate': True,
                    'stargazerCount': 5,
                    'primaryLanguage': {'name': 'C++'},
                    'defaultBranchRef': {
                        'target': {
                            'history': {
                                'edges': [
                                    {'node': {'messageHeadline': 'Add physics engine', 'committedDate': '2023-01-05T00:00:00Z'}}
                                ]
                            }
                        }
                    }
                }
            ]
    else:
        repos = get_repositories(token)

    new_content = generate_markdown(repos)

    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    pattern = r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)'

    new_readme_content = re.sub(
        pattern,
        lambda m: f'{m.group(1)}{new_content}{m.group(2)}',
        readme_content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme_content)

    print("README.md updated successfully.")

if __name__ == "__main__":
    main()
