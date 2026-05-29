import os
import requests
import json

# Configuration
GITHUB_TOKEN = os.environ.get("GH_TOKEN")
USERNAME = "LaTortu3"
GRAPHQL_URL = "https://api.github.com/graphql"

def fetch_repos():
    """Fetches repositories using GitHub GraphQL API."""
    if not GITHUB_TOKEN:
        print("GH_TOKEN not found, using mock data for local testing.")
        return get_mock_data()

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    {
      user(login: "%s") {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
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
    """ % USERNAME

    response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['user']['repositories']['nodes']
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {query}")

def get_mock_data():
    """Returns mock data for testing without a token."""
    return [
        {
            "name": "mock-repo-1",
            "url": "https://github.com/LaTortu3/mock-repo-1",
            "isPrivate": False,
            "stargazerCount": 5,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Initial commit", "committedDate": "2023-10-26T10:00:00Z"}},
                            {"node": {"messageHeadline": "Update README", "committedDate": "2023-10-27T12:00:00Z"}}
                        ]
                    }
                }
            }
        },
        {
            "name": "secret-project",
            "url": "https://github.com/LaTortu3/secret-project",
            "isPrivate": True,
            "stargazerCount": 0,
            "primaryLanguage": {"name": "Lua"},
             "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "WIP: Core logic", "committedDate": "2023-10-28T10:00:00Z"}}
                        ]
                    }
                }
            }
        }
    ]

def generate_markdown(repos):
    """Generates markdown string from repository data."""
    md = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        is_private = "🔒 Private" if repo['isPrivate'] else "🌍 Public"
        stars = repo['stargazerCount']
        lang = repo['primaryLanguage']['name'] if repo.get('primaryLanguage') else "N/A"

        md += f"#### [{name}]({url}) - {is_private}\n"
        md += f"**Language:** {lang} | **Stars:** ⭐ {stars}\n"
        md += "**Recent Commits:**\n"

        if repo.get('defaultBranchRef') and repo['defaultBranchRef'].get('target'):
            commits = repo['defaultBranchRef']['target']['history']['edges']
            if commits:
                for commit_edge in commits:
                    commit = commit_edge['node']
                    msg = commit['messageHeadline']
                    date = commit['committedDate'][:10]
                    md += f"- `{date}`: {msg}\n"
            else:
                md += "- No recent commits.\n"
        else:
            md += "- Repository is empty or has no commits.\n"
        md += "\n"
    return md

def update_readme(markdown_content):
    """Injects the markdown content into README.md."""
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    start_index = readme.find(start_marker)
    end_index = readme.find(end_marker)

    if start_index == -1 or end_index == -1:
        print("Markers not found in README.md")
        return

    new_readme = readme[:start_index + len(start_marker)] + "\n" + markdown_content + readme[end_index:]

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)
        print("README.md updated successfully.")

if __name__ == "__main__":
    repos_data = fetch_repos()
    generated_md = generate_markdown(repos_data)
    update_readme(generated_md)
