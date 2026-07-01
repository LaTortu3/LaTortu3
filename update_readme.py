import os
import requests
import re
from datetime import datetime

# Configuration
GITHUB_TOKEN = os.getenv("GH_TOKEN")
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"
README_FILE = "README.md"
API_URL = "https://api.github.com/graphql"

def get_repositories():
    if not GITHUB_TOKEN:
        if IS_GITHUB_ACTIONS:
            raise ValueError("GH_TOKEN environment variable is missing in GitHub Actions!")
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

    response = requests.post(API_URL, json={"query": query}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

    result = response.json()
    if 'errors' in result:
        raise Exception(f"GraphQL errors: {result['errors']}")

    return result["data"]["viewer"]["repositories"]["nodes"]

def get_mock_data():
    return [
        {
            "name": "mock-repo-1",
            "url": "https://github.com/LaTortu3/mock-repo-1",
            "visibility": "PUBLIC",
            "stargazerCount": 42,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T10:00:00Z"},
                            {"messageHeadline": "Add feature X", "committedDate": "2023-10-28T14:30:00Z"}
                        ]
                    }
                }
            }
        },
        {
            "name": "private-lua-project",
            "url": "https://github.com/LaTortu3/private-lua-project",
            "visibility": "PRIVATE",
            "stargazerCount": 0,
            "primaryLanguage": {"name": "Lua"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Update gameplay loop", "committedDate": "2023-11-01T09:15:00Z"}
                        ]
                    }
                }
            }
        }
    ]

def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def generate_markdown(repos):
    markdown = ""
    for repo in repos:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        visibility = repo.get("visibility", "PUBLIC").capitalize()
        stars = repo.get("stargazerCount", 0)

        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name") if lang_node else "N/A"

        markdown += f"#### 📁 [{name}]({url}) `[{visibility}]`\n"
        markdown += f"- **Langage principal :** {lang}\n"
        markdown += f"- **Stars :** ⭐ {stars}\n"

        markdown += "- **Derniers commits :**\n"

        branch_ref = repo.get("defaultBranchRef")
        if branch_ref and branch_ref.get("target") and branch_ref["target"].get("history") and branch_ref["target"]["history"].get("nodes"):
            commits = branch_ref["target"]["history"]["nodes"]
            for commit in commits:
                msg = commit.get("messageHeadline", "Sans message")
                date = format_date(commit.get("committedDate"))
                markdown += f"  - `{date}` : {msg}\n"
        else:
            markdown += "  - Aucun commit récent trouvé.\n"

        markdown += "\n"

    return markdown.strip()

def update_readme(new_content):
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # We use a lambda to avoid issues with backreferences in the replacement string
    updated_content = re.sub(
        pattern,
        lambda m: f"{m.group(1)}\n{new_content}\n\n{m.group(2)}",
        content,
        flags=re.DOTALL
    )

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)

if __name__ == "__main__":
    print("Fetching repositories...")
    repos = get_repositories()
    print(f"Found {len(repos)} repositories.")

    print("Generating markdown...")
    markdown_content = generate_markdown(repos)

    print("Updating README.md...")
    update_readme(markdown_content)

    print("Update complete!")
