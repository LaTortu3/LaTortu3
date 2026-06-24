import os
import re
import requests
from datetime import datetime

# Define GraphQL endpoint
GITHUB_API_URL = "https://api.github.com/graphql"

# Define GraphQL query
query = """
query {
  viewer {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, isFork: false) {
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

def fetch_repos():
    token = os.environ.get("GH_TOKEN")

    if not token:
        if os.environ.get("GITHUB_ACTIONS") == "true":
            raise ValueError("GH_TOKEN environment variable is missing in GitHub Actions environment. Aborting to prevent mock data injection.")
        else:
            print("Warning: GH_TOKEN not found. Falling back to mock data for local testing.")
            return get_mock_data()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(GITHUB_API_URL, json={'query': query}, headers=headers)
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
                            {"node": {"messageHeadline": "Initial commit", "committedDate": "2023-10-01T12:00:00Z"}},
                            {"node": {"messageHeadline": "Update README", "committedDate": "2023-10-02T12:00:00Z"}}
                        ]
                    }
                }
            }
        },
        {
            "name": "mock-private-repo",
            "url": "https://github.com/LaTortu3/mock-private-repo",
            "visibility": "PRIVATE",
            "stargazerCount": 0,
            "primaryLanguage": {"name": "C++"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Fix engine bug", "committedDate": "2023-10-05T15:30:00Z"}},
                        ]
                    }
                }
            }
        }
    ]

def format_date(date_str):
    date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
    return date_obj.strftime("%d/%m/%Y")

def generate_markdown(repos):
    markdown = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        visibility = repo['visibility']
        stars = repo['stargazerCount']
        lang = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "N/A"

        markdown += f"#### 🔹 [{name}]({url}) - ⭐ {stars} | 🔒 {visibility} | 🔤 {lang}\n"

        commits = []
        if repo.get('defaultBranchRef') and repo['defaultBranchRef'].get('target') and repo['defaultBranchRef']['target'].get('history'):
            edges = repo['defaultBranchRef']['target']['history']['edges']
            for edge in edges:
                msg = edge['node']['messageHeadline']
                date = format_date(edge['node']['committedDate'])
                commits.append(f"  - `{date}` : {msg}")

        if commits:
            markdown += "\n".join(commits) + "\n\n"
        else:
            markdown += "  - _Aucun commit récent_\n\n"

    return markdown

def update_readme(markdown_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # Lambda function to prevent backreference parsing errors with replacement strings
    def replacer(match):
        return f"{match.group(1)}{markdown_content}{match.group(2)}"

    updated_readme = re.sub(pattern, replacer, readme, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print("README.md updated successfully!")

if __name__ == "__main__":
    repos = fetch_repos()
    markdown = generate_markdown(repos)
    update_readme(markdown)
