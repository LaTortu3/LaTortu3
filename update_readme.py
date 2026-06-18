import os
import requests

GITHUB_TOKEN = os.environ.get("GH_TOKEN")
IS_GITHUB_ACTIONS = os.environ.get("GITHUB_ACTIONS") == "true"

def fetch_repos():
    if not GITHUB_TOKEN:
        if IS_GITHUB_ACTIONS:
            raise ValueError("GH_TOKEN is missing in GitHub Actions environment.")
        print("GH_TOKEN is missing. Using mock data.")
        return get_mock_data()

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
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
    if response.status_code == 200:
        return response.json()['data']['viewer']['repositories']['nodes']
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def get_mock_data():
    return [
        {
            "name": "mock-repo-1",
            "url": "https://github.com/LaTortu3/mock-repo-1",
            "visibility": "PUBLIC",
            "stargazerCount": 5,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T10:00:00Z"}},
                            {"node": {"messageHeadline": "Add feature X", "committedDate": "2023-10-26T10:00:00Z"}},
                            {"node": {"messageHeadline": "Fix bug Y", "committedDate": "2023-10-25T10:00:00Z"}}
                        ]
                    }
                }
            }
        },
        {
             "name": "mock-repo-2",
             "url": "https://github.com/LaTortu3/mock-repo-2",
             "visibility": "PRIVATE",
             "stargazerCount": 0,
             "primaryLanguage": {"name": "Lua"},
             "defaultBranchRef": {
                 "target": {
                     "history": {
                         "edges": [
                             {"node": {"messageHeadline": "Update logic", "committedDate": "2023-10-24T10:00:00Z"}}
                         ]
                     }
                 }
             }
        }
    ]

def format_repos_markdown(repos):
    markdown = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        visibility = repo['visibility']
        stars = repo['stargazerCount']

        lang_info = repo.get('primaryLanguage')
        lang = lang_info['name'] if lang_info else 'N/A'

        markdown += f"### 🔗 [{name}]({url})\n"
        markdown += f"**Visibilité:** {visibility} | **⭐ Étoiles:** {stars} | **Langage Principal:** {lang}\n\n"

        branch_ref = repo.get('defaultBranchRef')
        if branch_ref and branch_ref.get('target') and branch_ref['target'].get('history'):
            commits = branch_ref['target']['history']['edges']
            if commits:
                markdown += "**Derniers Commits :**\n"
                for commit_edge in commits:
                    commit = commit_edge['node']
                    message = commit['messageHeadline']
                    date = commit['committedDate'][:10]
                    markdown += f"- `{date}` : {message}\n"
        markdown += "\n---\n\n"
    return markdown

def update_readme(markdown_content):
    import re
    with open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()

    # We use a lambda to avoid backreference parsing errors with replacement string
    pattern = re.compile(r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)', re.DOTALL)
    updated_readme = pattern.sub(lambda m: f"{m.group(1)}{markdown_content}{m.group(2)}", readme)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(updated_readme)
    print("README.md updated successfully.")

if __name__ == "__main__":
    repos = fetch_repos()
    print(f"Fetched {len(repos)} repositories.")
    markdown_content = format_repos_markdown(repos)
    update_readme(markdown_content)
