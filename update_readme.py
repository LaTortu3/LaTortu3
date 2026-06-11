import os
import requests
import json
import re

# GitHub GraphQL API Endpoint
GRAPHQL_URL = "https://api.github.com/graphql"

def fetch_repos(token):
    """Fetches up to 100 repositories for the authenticated user using GraphQL."""
    query = """
    query {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            visibility
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
                      oid
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
        "Content-Type": "application/json"
    }

    response = requests.post(GRAPHQL_URL, headers=headers, json={"query": query})

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def get_mock_data():
    """Returns mock data for local testing when GH_TOKEN is missing."""
    return {
        "data": {
            "viewer": {
                "repositories": {
                    "nodes": [
                        {
                            "name": "mock-repo-1",
                            "visibility": "PUBLIC",
                            "stargazerCount": 10,
                            "primaryLanguage": {"name": "Python"},
                            "url": "https://github.com/LaTortu3/mock-repo-1",
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Initial commit", "oid": "abc1234", "committedDate": "2024-01-01T12:00:00Z"},
                                            {"messageHeadline": "Update README", "oid": "def5678", "committedDate": "2024-01-02T12:00:00Z"}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            "name": "private-mock-repo",
                            "visibility": "PRIVATE",
                            "stargazerCount": 5,
                            "primaryLanguage": {"name": "JavaScript"},
                            "url": "https://github.com/LaTortu3/private-mock-repo",
                            "defaultBranchRef": {
                                "target": {
                                    "history": {
                                        "nodes": [
                                            {"messageHeadline": "Fix login bug", "oid": "ghi9012", "committedDate": "2024-01-03T12:00:00Z"}
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

def format_repo_markdown(repo):
    """Formats repository data into a Markdown list item."""
    name = repo.get("name", "Unknown")
    url = repo.get("url", "#")
    visibility = repo.get("visibility", "PUBLIC").capitalize()
    stars = repo.get("stargazerCount", 0)
    lang = repo.get("primaryLanguage")
    language_name = lang.get("name", "N/A") if lang else "N/A"

    md = f"#### 📁 [{name}]({url}) - `{visibility}` | ⭐ {stars} | 🔵 {language_name}\n"

    # Extract commit history if available
    default_branch = repo.get("defaultBranchRef")
    if default_branch and default_branch.get("target") and default_branch["target"].get("history"):
        commits = default_branch["target"]["history"].get("nodes", [])
        if commits:
            md += "<ul>\n"
            for commit in commits:
                msg = commit.get("messageHeadline", "No message")
                date = commit.get("committedDate", "")[:10]  # Just the date part
                md += f"  <li><em>{date}</em> : {msg}</li>\n"
            md += "</ul>\n"
        else:
            md += "  - *No commits found.*\n"
    else:
        md += "  - *No commit history available.*\n"

    return md + "\n"

def update_readme(new_content):
    """Reads README.md, replaces the dynamic block, and writes it back."""
    readme_path = "README.md"

    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print("README.md not found.")
        return

    # Regular expression to find the start and end markers and everything in between
    pattern = re.compile(
        r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)",
        re.DOTALL
    )

    # Replace the matched section with the new content using a lambda to avoid backreference issues
    updated_content = pattern.sub(lambda m: m.group(1) + new_content + m.group(2), content)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("README.md successfully updated!")

def main():
    token = os.environ.get("GH_TOKEN")
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_ci:
            raise Exception("GH_TOKEN is missing in the GitHub Actions environment. Aborting to prevent mock data injection.")
        else:
            print("GH_TOKEN not found. Using mock data for local testing.")
            data = get_mock_data()
    else:
        print("GH_TOKEN found. Fetching data from GitHub...")
        data = fetch_repos(token)

    repos = data.get("data", {}).get("viewer", {}).get("repositories", {}).get("nodes", [])

    if not repos:
        print("No repositories found.")
        markdown_content = "_No repositories found._\n"
    else:
        markdown_content = ""
        for repo in repos:
            markdown_content += format_repo_markdown(repo)

    update_readme(markdown_content)

if __name__ == "__main__":
    main()
