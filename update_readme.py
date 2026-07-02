import os
import re
import requests

def fetch_github_data(token):
    query = """
    query {
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
    }
    """

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['viewer']['repositories']['nodes']
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def get_mock_data():
    return [
        {
            "name": "Unreal-Engine-Game",
            "url": "https://github.com/LaTortu3/Unreal-Engine-Game",
            "visibility": "PUBLIC",
            "stargazerCount": 42,
            "primaryLanguage": {"name": "C++"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Implement new gameplay logic", "committedDate": "2023-10-27T10:00:00Z"}},
                            {"node": {"messageHeadline": "Fix memory leak in physics engine", "committedDate": "2023-10-26T15:30:00Z"}},
                            {"node": {"messageHeadline": "Update Lua integration scripts", "committedDate": "2023-10-25T09:15:00Z"}}
                        ]
                    }
                }
            }
        },
        {
            "name": "React-Portfolio",
            "url": "https://github.com/LaTortu3/React-Portfolio",
            "visibility": "PRIVATE",
            "stargazerCount": 10,
            "primaryLanguage": {"name": "JavaScript"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Add new project section", "committedDate": "2023-10-24T14:20:00Z"}},
                            {"node": {"messageHeadline": "Update styling for mobile", "committedDate": "2023-10-23T11:45:00Z"}}
                        ]
                    }
                }
            }
        }
    ]

def get_repo_data():
    token = os.environ.get("GH_TOKEN")
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise ValueError("GH_TOKEN is missing in GitHub Actions environment. Aborting to prevent mock data injection.")
        print("GH_TOKEN not found. Using mock data for local testing.")
        return get_mock_data()

    print("Fetching data from GitHub API...")
    return fetch_github_data(token)

def generate_markdown(repos):
    md = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        visibility = repo['visibility'].lower().capitalize()
        stars = repo['stargazerCount']
        lang = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "N/A"

        md += f"#### [{name}]({url}) 🌟 {stars} | 🔒 {visibility} | 🔤 {lang}\n"

        commits = []
        if repo['defaultBranchRef'] and repo['defaultBranchRef']['target'] and 'history' in repo['defaultBranchRef']['target']:
             commits = repo['defaultBranchRef']['target']['history']['edges']

        if commits:
            md += "- **Derniers Commits :**\n"
            for commit_edge in commits:
                commit = commit_edge['node']
                message = commit['messageHeadline']
                date = commit['committedDate'][:10]
                md += f"  - `{date}` : {message}\n"
        else:
            md += "- *Aucun commit récent.*\n"
        md += "\n"
    return md

def update_readme(new_content):
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)'

    # Lambda substitution to avoid backreference errors in regex
    updated_content = re.sub(
        pattern,
        lambda m: f'{m.group(1)}\n{new_content}\n{m.group(2)}',
        content,
        flags=re.DOTALL
    )

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    print("README.md updated successfully.")

if __name__ == "__main__":
    try:
        repos = get_repo_data()
        markdown_content = generate_markdown(repos)
        update_readme(markdown_content)
    except Exception as e:
        print(f"Error updating README: {e}")
        exit(1)
