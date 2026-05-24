import os
import requests
import json
import re

GITHUB_USERNAME = 'LaTortu3'
GH_TOKEN = os.environ.get('GH_TOKEN')

GRAPHQL_QUERY = """
query {
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, privacy: PUBLIC) {
      nodes {
        name
        stargazerCount
        primaryLanguage {
          name
        }
        isPrivate
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
""" % GITHUB_USERNAME

# We will need to query for both public and private repositories if needed.
# We can use the generic owner(login: "%s") and search for both if the token has access.

GRAPHQL_QUERY_AUTHED = """
query {
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: [OWNER]) {
      nodes {
        name
        stargazerCount
        primaryLanguage {
          name
        }
        isPrivate
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
""" % GITHUB_USERNAME


def fetch_github_data():
    if not GH_TOKEN:
        print("No GH_TOKEN found. Using mock data.")
        return {
            "data": {
                "user": {
                    "repositories": {
                        "nodes": [
                            {
                                "name": "mock-repo-1",
                                "stargazerCount": 42,
                                "primaryLanguage": {"name": "Python"},
                                "isPrivate": False,
                                "defaultBranchRef": {
                                    "target": {
                                        "history": {
                                            "edges": [
                                                {"node": {"messageHeadline": "Initial commit", "committedDate": "2024-01-01T00:00:00Z"}},
                                                {"node": {"messageHeadline": "Add features", "committedDate": "2024-01-02T00:00:00Z"}},
                                            ]
                                        }
                                    }
                                }
                            },
                            {
                                "name": "secret-project",
                                "stargazerCount": 10,
                                "primaryLanguage": {"name": "C++"},
                                "isPrivate": True,
                                "defaultBranchRef": {
                                    "target": {
                                        "history": {
                                            "edges": [
                                                {"node": {"messageHeadline": "Fix bugs", "committedDate": "2024-02-01T00:00:00Z"}},
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

    headers = {
        "Authorization": f"bearer {GH_TOKEN}",
        "Content-Type": "application/json"
    }

    print("Fetching data from GitHub API...")
    response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json={"query": GRAPHQL_QUERY_AUTHED}
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data: {response.status_code}")
        print(response.text)
        return None

def process_data(data):
    if not data or 'data' not in data or 'user' not in data['data'] or not data['data']['user']:
        return "<!-- No repositories found or API limit reached -->"

    nodes = data['data']['user']['repositories']['nodes']
    markdown_lines = []

    for repo in nodes:
        name = repo.get('name', 'Unknown')
        stars = repo.get('stargazerCount', 0)

        # Primary Language
        primary_lang = repo.get('primaryLanguage')
        lang_str = primary_lang.get('name') if primary_lang else 'Unknown'

        # Private/Public status
        is_private = repo.get('isPrivate', False)
        privacy_badge = "🔒 Private" if is_private else "🌍 Public"

        markdown_lines.append(f"#### 📦 {name}")
        markdown_lines.append(f"- **Language:** {lang_str} | **Stars:** ⭐ {stars} | **Status:** {privacy_badge}")

        # Commits
        branch_ref = repo.get('defaultBranchRef')
        if branch_ref and branch_ref.get('target') and branch_ref['target'].get('history'):
            commits = branch_ref['target']['history']['edges']
            if commits:
                markdown_lines.append("- **Last Commits:**")
                for commit in commits:
                    msg = commit['node']['messageHeadline']
                    date = commit['node']['committedDate'][:10]
                    markdown_lines.append(f"  - `{date}`: {msg}")
            else:
                markdown_lines.append("- *No recent commits found.*")
        else:
            markdown_lines.append("- *No recent commits found.*")

        markdown_lines.append("<br>\n")

    return "\n".join(markdown_lines)

def update_readme(markdown_content):
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_data = f.read()
    except FileNotFoundError:
        print("README.md not found.")
        return

    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # Use lambda to avoid regex parsing issues if markdown_content contains \g or \1
    new_readme_data = re.sub(pattern, lambda m: f"{m.group(1)}{markdown_content}\n{m.group(2)}", readme_data, flags=re.DOTALL)

    if new_readme_data == readme_data:
         print("No changes made to README.md. Markers might be missing.")
         return

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_readme_data)
    print("README.md successfully updated!")

if __name__ == "__main__":
    data = fetch_github_data()
    if data:
        markdown = process_data(data)
        update_readme(markdown)
