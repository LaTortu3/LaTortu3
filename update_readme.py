import os
import requests
import re
from datetime import datetime

# GitHub GraphQL API URL
GITHUB_API_URL = "https://api.github.com/graphql"

# Token handling
token = os.environ.get("GH_TOKEN")
is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

if not token:
    if is_github_actions:
        raise ValueError("GH_TOKEN is missing. Cannot fetch repositories in GitHub Actions environment.")
    else:
        print("GH_TOKEN is missing. Running in local mode with mock data.")
        use_mock_data = True
else:
    use_mock_data = False

# GraphQL query to fetch viewer's repositories
query = """
{
  viewer {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
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

def fetch_repositories():
    if use_mock_data:
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
                            "nodes": [
                                {"messageHeadline": "Initial commit", "committedDate": "2023-10-26T10:00:00Z"},
                                {"messageHeadline": "Update README", "committedDate": "2023-10-27T10:00:00Z"}
                            ]
                        }
                    }
                }
            },
             {
                "name": "mock-repo-2",
                "url": "https://github.com/LaTortu3/mock-repo-2",
                "visibility": "PRIVATE",
                "stargazerCount": 2,
                "primaryLanguage": {"name": "JavaScript"},
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "nodes": [
                                {"messageHeadline": "Initial commit", "committedDate": "2023-10-25T10:00:00Z"}
                            ]
                        }
                    }
                }
            }
        ]

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(GITHUB_API_URL, json={"query": query}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
             raise Exception(f"GraphQL errors: {data['errors']}")
        return data["data"]["viewer"]["repositories"]["nodes"]
    else:
        raise Exception(f"Failed to fetch repositories: {response.status_code} - {response.text}")


def format_repositories(repositories):
    content = ""
    for repo in repositories:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        visibility = repo.get("visibility", "PUBLIC").lower()
        stars = repo.get("stargazerCount", 0)

        primary_lang = repo.get("primaryLanguage")
        lang_str = primary_lang.get("name", "Unknown") if primary_lang else "Unknown"

        content += f"#### [{name}]({url}) ({visibility})\n"
        content += f"⭐ {stars} stars | 💻 {lang_str}\n\n"

        default_branch = repo.get("defaultBranchRef")
        if default_branch and default_branch.get("target") and default_branch["target"].get("history"):
            commits = default_branch["target"]["history"].get("nodes", [])
            if commits:
                content += "##### Récents Commits :\n"
                for commit in commits:
                    msg = commit.get("messageHeadline", "")
                    date_str = commit.get("committedDate", "")

                    if date_str:
                         try:
                             # Try parsing GitHub's ISO 8601 format
                             date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                             date_formatted = date_obj.strftime("%d %b %Y")
                         except ValueError:
                             date_formatted = date_str
                    else:
                         date_formatted = "Unknown"

                    content += f"- `{date_formatted}` : {msg}\n"
        content += "\n---\n\n"
    return content

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Find the markers and replace the content
    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # Use a lambda to avoid issues with backreferences in new_content
    updated_readme = re.sub(
        pattern,
        lambda m: f"{m.group(1)}{new_content}{m.group(2)}",
        readme_content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print("README.md successfully updated!")


if __name__ == "__main__":
    print("Fetching repositories...")
    repos = fetch_repositories()
    print(f"Found {len(repos)} repositories.")

    print("Formatting repository data...")
    markdown_content = format_repositories(repos)

    print("Updating README.md...")
    update_readme(markdown_content)
