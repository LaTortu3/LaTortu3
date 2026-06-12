import os
import re
import requests
import json

def fetch_repos(token):
    # GraphQL query to fetch viewer's repositories
    query = """
    {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
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

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def format_repo_data(data):
    # Extract nodes
    try:
        repos = data["data"]["viewer"]["repositories"]["nodes"]
    except KeyError:
         repos = []

    formatted_content = ""
    for repo in repos:
        name = repo.get("name", "Unknown Repo")
        url = repo.get("url", f"https://github.com/LaTortu3/{name}")
        visibility = "🔒 Private" if repo.get("isPrivate") else "🌍 Public"
        stars = repo.get("stargazerCount", 0)

        primary_lang = repo.get("primaryLanguage")
        language = primary_lang.get("name") if primary_lang else "N/A"

        formatted_content += f"#### [{name}]({url})\n"
        formatted_content += f"- **Visibility:** {visibility} | **Stars:** {stars} ⭐ | **Language:** {language}\n"

        commits_content = "- **Last 3 Commits:**\n"

        try:
             commits = repo["defaultBranchRef"]["target"]["history"]["nodes"]
             for commit in commits:
                 message = commit.get("messageHeadline", "No message")
                 date = commit.get("committedDate", "Unknown date")[:10] # Get YYYY-MM-DD
                 commits_content += f"  - `{date}`: {message}\n"
        except (KeyError, TypeError):
             commits_content += "  - No recent commits available.\n"

        formatted_content += commits_content + "\n"

    return formatted_content

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    # The markers to find
    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    # Regex to replace the content between the markers
    pattern = re.compile(rf"({start_marker}).*?({end_marker})", re.DOTALL)

    if pattern.search(readme_content):
        updated_readme = pattern.sub(lambda m: f"{m.group(1)}\n{new_content}{m.group(2)}", readme_content)
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(updated_readme)
        print("README.md successfully updated!")
    else:
        print("Markers not found in README.md.")


def main():
    # Check if we are in GitHub Actions
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"
    token = os.environ.get("GH_TOKEN")

    if not token:
        if is_github_actions:
            raise Exception("GH_TOKEN is missing in a GitHub Actions environment!")
        else:
            print("GH_TOKEN is missing. Using mock data for local testing.")
            # Fallback mock data
            mock_data = {
                "data": {
                    "viewer": {
                        "repositories": {
                            "nodes": [
                                {
                                    "name": "MockRepo-Public",
                                    "url": "https://github.com/LaTortu3/MockRepo-Public",
                                    "isPrivate": False,
                                    "stargazerCount": 42,
                                    "primaryLanguage": {"name": "Python"},
                                    "defaultBranchRef": {
                                        "target": {
                                            "history": {
                                                "nodes": [
                                                    {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T10:00:00Z"},
                                                    {"messageHeadline": "Update README", "committedDate": "2023-10-28T10:00:00Z"},
                                                    {"messageHeadline": "Fix a bug", "committedDate": "2023-10-29T10:00:00Z"}
                                                ]
                                            }
                                        }
                                    }
                                },
                                {
                                    "name": "MockRepo-Private",
                                    "url": "https://github.com/LaTortu3/MockRepo-Private",
                                    "isPrivate": True,
                                    "stargazerCount": 5,
                                    "primaryLanguage": {"name": "JavaScript"},
                                    "defaultBranchRef": {
                                        "target": {
                                            "history": {
                                                "nodes": [
                                                    {"messageHeadline": "Secret commit", "committedDate": "2023-10-30T10:00:00Z"}
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
            formatted_content = format_repo_data(mock_data)
            update_readme(formatted_content)
            return

    # If token exists, fetch data from GitHub API
    try:
         data = fetch_repos(token)
         formatted_content = format_repo_data(data)
         update_readme(formatted_content)
    except Exception as e:
         print(f"Error fetching data: {e}")
         raise

if __name__ == "__main__":
    main()
