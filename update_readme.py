import os
import re
import requests
from typing import List, Dict

# GitHub GraphQL API endpoint
GITHUB_API_URL = "https://api.github.com/graphql"

def fetch_repositories(token: str) -> List[Dict]:
    """Fetches up to 100 recent repositories for the authenticated user using GraphQL."""
    query = """
    query {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: [OWNER]) {
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

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(GITHUB_API_URL, json={"query": query}, headers=headers)
    response.raise_for_status()

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")

    return data["data"]["viewer"]["repositories"]["nodes"]

def generate_mock_data() -> List[Dict]:
    """Generates mock repository data for local testing when no token is provided."""
    return [
        {
            "name": "Super-Game-Engine",
            "url": "https://github.com/LaTortu3/Super-Game-Engine",
            "isPrivate": False,
            "stargazerCount": 42,
            "primaryLanguage": {"name": "C++"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Add physics engine", "pushedDate": "2023-10-27T10:00:00Z"}},
                            {"node": {"messageHeadline": "Fix rendering bug", "pushedDate": "2023-10-25T14:30:00Z"}},
                            {"node": {"messageHeadline": "Initial commit", "pushedDate": "2023-10-20T09:15:00Z"}}
                        ]
                    }
                }
            }
        },
        {
            "name": "React-Portfolio",
            "url": "https://github.com/LaTortu3/React-Portfolio",
            "isPrivate": True,
            "stargazerCount": 5,
            "primaryLanguage": {"name": "JavaScript"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Update styling", "pushedDate": "2023-10-26T16:45:00Z"}}
                        ]
                    }
                }
            }
        }
    ]

def format_repo_markdown(repo: Dict) -> str:
    """Formats a single repository's data into Markdown."""
    name = repo.get("name", "Unknown Repo")
    url = repo.get("url", "#")
    is_private = repo.get("isPrivate", False)
    stars = repo.get("stargazerCount", 0)

    lang_info = repo.get("primaryLanguage")
    lang = lang_info.get("name") if lang_info else "N/A"

    visibility_badge = "🔒 Private" if is_private else "🌍 Public"

    markdown = f"#### [{name}]({url}) - {visibility_badge} - ⭐ {stars} - 💻 {lang}\n"

    commits = []
    try:
        edges = repo["defaultBranchRef"]["target"]["history"]["edges"]
        for edge in edges:
            node = edge["node"]
            msg = node.get("messageHeadline", "No message")
            date = node.get("committedDate", "")[:10]  # Just grab YYYY-MM-DD
            if date:
                commits.append(f"  - `{date}`: {msg}")
            else:
                 commits.append(f"  - {msg}")
    except (KeyError, TypeError):
        pass

    if commits:
        markdown += "\n".join(commits) + "\n"
    else:
        markdown += "  - No recent commits available.\n"

    return markdown + "\n"

def update_readme(content_to_inject: str):
    """Injects the generated Markdown into the README.md file."""
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Regex to find the dynamic markers and replace the content between them
    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # Use a lambda to avoid issues with backreferences in the replacement string
    new_readme = re.sub(
        pattern,
        lambda m: f"{m.group(1)}{content_to_inject}{m.group(2)}",
        readme_content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

    print("README.md successfully updated!")

def main():
    token = os.environ.get("GH_TOKEN")
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise ValueError("GH_TOKEN environment variable is missing in GitHub Actions environment. Cannot fetch data.")
        else:
            print("GH_TOKEN not found. Using mock data for local testing.")
            repos = generate_mock_data()
    else:
        print("Fetching repositories from GitHub API...")
        repos = fetch_repositories(token)
        print(f"Fetched {len(repos)} repositories.")

    markdown_content = ""
    for repo in repos:
        markdown_content += format_repo_markdown(repo)

    update_readme(markdown_content)

if __name__ == "__main__":
    main()
