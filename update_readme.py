import os
import requests
import re
from datetime import datetime

# Configuration
GITHUB_TOKEN = os.getenv("GH_TOKEN")
USERNAME = "LaTortu3"
README_FILE = "README.md"
START_MARKER = "<!-- DYNAMIC_REPOS_START -->"
END_MARKER = "<!-- DYNAMIC_REPOS_END -->"

GRAPHQL_QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, privacy: PUBLIC) {
      nodes {
        name
        isPrivate
        stargazerCount
        primaryLanguage {
          name
        }
        pushedAt
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
""" % USERNAME

# Try fetching repositories from both PUBLIC and PRIVATE if token allows, otherwise we just fetch all available to the token.
GRAPHQL_QUERY_ALL = """
{
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        isPrivate
        stargazerCount
        primaryLanguage {
          name
        }
        pushedAt
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 3) {
                nodes {
                  messageHeadline
                  committedDate
                  oid
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


def get_repositories():
    if not GITHUB_TOKEN:
        print("Warning: GH_TOKEN not found. Using mock data for local testing.")
        return get_mock_repositories()

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": GRAPHQL_QUERY_ALL},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            print(f"GraphQL errors: {data['errors']}")
            return []

        return data["data"]["user"]["repositories"]["nodes"]
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from GitHub API: {e}")
        return []

def get_mock_repositories():
    return [
        {
            "name": "Unreal-Engine-Lua-Integration",
            "isPrivate": False,
            "stargazerCount": 42,
            "primaryLanguage": {"name": "C++"},
            "pushedAt": datetime.now().isoformat(),
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Add Lua script execution component", "committedDate": "2024-06-01T12:00:00Z"},
                            {"messageHeadline": "Update README with setup instructions", "committedDate": "2024-05-30T10:00:00Z"},
                            {"messageHeadline": "Initial commit for UE5 plugin", "committedDate": "2024-05-25T15:00:00Z"}
                        ]
                    }
                }
            }
        },
        {
            "name": "react-portfolio-site",
            "isPrivate": True,
            "stargazerCount": 0,
            "primaryLanguage": {"name": "JavaScript"},
            "pushedAt": datetime.now().isoformat(),
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Fix layout issues on mobile", "committedDate": "2024-06-03T09:00:00Z"},
                            {"messageHeadline": "Add dynamic repo list component", "committedDate": "2024-06-02T14:30:00Z"}
                        ]
                    }
                }
            }
        },
        {
            "name": "auto-readme-updater",
            "isPrivate": False,
            "stargazerCount": 15,
            "primaryLanguage": {"name": "Python"},
            "pushedAt": datetime.now().isoformat(),
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Implement GraphQL API fetching", "committedDate": "2024-06-04T16:00:00Z"},
                            {"messageHeadline": "Setup GitHub Actions workflow", "committedDate": "2024-06-04T10:00:00Z"}
                        ]
                    }
                }
            }
        }
    ]

def format_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        # Some mock dates or other formats might include milliseconds or timezone offsets differently
        try:
            # Fallback for ISO format parsing if standard strict format fails
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            return date_str

def generate_markdown(repositories):
    if not repositories:
        return "*Aucun dépôt trouvé ou erreur lors de la récupération des données.*\n"

    markdown = "\n"
    for repo in repositories:
        if repo is None:
            continue

        name = repo.get("name", "Unknown Repo")
        is_private = repo.get("isPrivate", False)
        stars = repo.get("stargazerCount", 0)
        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name", "N/A") if lang_node else "N/A"

        visibility = "🔒 Privé" if is_private else "🌍 Public"
        star_icon = "⭐"

        markdown += f"#### [{name}](https://github.com/{USERNAME}/{name}) - {visibility}\n"
        markdown += f"> **Langage:** {lang} | **Stars:** {stars} {star_icon}\n"

        # Commits
        default_branch = repo.get("defaultBranchRef")
        if default_branch and default_branch.get("target") and default_branch["target"].get("history") and default_branch["target"]["history"].get("nodes"):
            commits = default_branch["target"]["history"]["nodes"]
            markdown += "> **Derniers Commits :**\n"
            for commit in commits:
                msg = commit.get("messageHeadline", "").strip()
                date = format_date(commit.get("committedDate", ""))
                markdown += f"> - `{date}` : {msg}\n"
        else:
            markdown += "> - *Aucun commit récent trouvé.*\n"

        markdown += "\n"

    return markdown

def update_readme(markdown_content):
    if not os.path.exists(README_FILE):
        print(f"Error: {README_FILE} not found.")
        return False

    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(rf"{START_MARKER}.*?{END_MARKER}", re.DOTALL)

    if not pattern.search(content):
         print(f"Error: Markers {START_MARKER} and {END_MARKER} not found in {README_FILE}.")
         return False

    new_content = pattern.sub(f"{START_MARKER}\n{markdown_content}\n{END_MARKER}", content)

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md updated successfully!")
    return True

if __name__ == "__main__":
    print("Fetching repositories...")
    repos = get_repositories()
    print(f"Found {len(repos)} repositories.")

    print("Generating markdown...")
    md = generate_markdown(repos)

    print("Updating README.md...")
    update_readme(md)
