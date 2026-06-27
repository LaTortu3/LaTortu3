import os
import re
import requests
from datetime import datetime

# Define GraphQL query to get user's repositories
GRAPHQL_QUERY = """
query {
  viewer {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: [OWNER]) {
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
                nodes {
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
"""

def get_repos_from_github(token):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": GRAPHQL_QUERY},
        headers=headers
    )
    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")
    return response.json()

def get_mock_data():
    return {
        "data": {
            "viewer": {
                "repositories": {
                    "nodes": [
                        {
                            "name": "AwesomeProject",
                            "url": "https://github.com/LaTortu3/AwesomeProject",
                            "visibility": "PUBLIC",
                            "stargazerCount": 42,
                            "primaryLanguage": {"name": "Python"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Initial commit", "committedDate": "2023-01-01T12:00:00Z"},
                                            {"messageHeadline": "Added new feature", "committedDate": "2023-01-02T12:00:00Z"}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "name": "SecretApp",
                            "url": "https://github.com/LaTortu3/SecretApp",
                            "visibility": "PRIVATE",
                            "stargazerCount": 0,
                            "primaryLanguage": {"name": "JavaScript"},
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Fix bug", "committedDate": "2023-01-05T12:00:00Z"}
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

def format_repo(repo):
    name = repo.get("name", "Unknown")
    url = repo.get("url", "#")
    visibility = repo.get("visibility", "PUBLIC")
    stars = repo.get("stargazerCount", 0)

    lang_obj = repo.get("primaryLanguage")
    lang = lang_obj.get("name") if lang_obj else "N/A"

    # Format basic info
    md = f"#### 📁 [{name}]({url}) { '⭐ ' + str(stars) if stars > 0 else ''}\n"
    md += f"- **Language:** {lang} | **Visibility:** {visibility}\n"

    # Try to get commits
    commits = []
    try:
        nodes = repo["defaultBranchRef"]["target"]["history"]["nodes"]
        commits = nodes
    except (KeyError, TypeError):
        pass

    if commits:
        md += "- **Last Commits:**\n"
        for commit in commits:
            msg = commit.get("messageHeadline", "No message")
            date_str = commit.get("committedDate", "")
            date_formatted = ""
            if date_str:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                    date_formatted = dt.strftime("%Y-%m-%d")
                except ValueError:
                    date_formatted = date_str
            md += f"  - `{date_formatted}`: {msg}\n"
    else:
        md += "- *No recent commits found.*\n"

    return md

def update_readme(new_content):
    with open("README.md", "r") as f:
        content = f.read()

    # Define the pattern to find the dynamic section
    pattern = r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)'

    # Create lambda function to insert new_content and preserve exact formatting to prevent backreference parsing errors
    replacement = lambda m: f"{m.group(1)}{new_content}\n{m.group(2)}"

    new_readme = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open("README.md", "w") as f:
        f.write(new_readme)

def main():
    token = os.environ.get("GH_TOKEN")

    # Check if running in GitHub Actions
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise ValueError("GH_TOKEN environment variable is missing but running in GitHub Actions environment. Aborting to prevent mock data injection.")
        print("GH_TOKEN not found. Using mock data for local testing.")
        data = get_mock_data()
    else:
        print("Fetching data from GitHub API...")
        data = get_repos_from_github(token)

    repos = data["data"]["viewer"]["repositories"]["nodes"]

    formatted_content = ""
    for repo in repos:
        if repo:
            formatted_content += format_repo(repo) + "\n"

    update_readme(formatted_content)
    print("README.md updated successfully!")

if __name__ == "__main__":
    main()
