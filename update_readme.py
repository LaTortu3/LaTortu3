import os
import requests
import re
from datetime import datetime

TOKEN = os.getenv("GH_TOKEN")

GRAPHQL_QUERY = """
{
  viewer {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        isPrivate
        stargazerCount
        url
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
    # If not running in GitHub Actions and no token, use mock data for local dev
    is_github_actions = os.getenv("GITHUB_ACTIONS") == "true"

    if not TOKEN:
        if is_github_actions:
            raise ValueError("GH_TOKEN is missing in GitHub Actions environment. Aborting to prevent mock data injection.")
        print("GH_TOKEN not found. Using mock data for local testing.")
        return get_mock_data()

    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        response = requests.post(
            'https://api.github.com/graphql',
            json={'query': GRAPHQL_QUERY},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Errors: {data['errors']}")
            if is_github_actions:
                 raise RuntimeError(f"GraphQL Errors: {data['errors']}")
            return get_mock_data()
        return data['data']['viewer']['repositories']['nodes']
    except Exception as e:
        print(f"Error fetching data: {e}")
        if is_github_actions:
            raise e
        return get_mock_data()

def get_mock_data():
    return [
        {
            "name": "MyAwesomeProject",
            "isPrivate": False,
            "stargazerCount": 42,
            "url": "https://github.com/LaTortu3/MyAwesomeProject",
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Fix critical bug in core module", "committedDate": "2023-10-27T10:00:00Z"},
                            {"messageHeadline": "Update README with setup instructions", "committedDate": "2023-10-26T15:30:00Z"},
                            {"messageHeadline": "Initial commit", "committedDate": "2023-10-25T09:15:00Z"}
                        ]
                    }
                }
            }
        },
        {
            "name": "SecretGameEngine",
            "isPrivate": True,
            "stargazerCount": 0,
            "url": "https://github.com/LaTortu3/SecretGameEngine",
            "primaryLanguage": {"name": "C++"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Optimize rendering pipeline", "committedDate": "2023-10-28T18:45:00Z"},
                            {"messageHeadline": "Implement basic physics loop", "committedDate": "2023-10-20T11:20:00Z"}
                        ]
                    }
                }
            }
        }
    ]

def format_repo_markdown(repo):
    visibility_badge = "🔒 Private" if repo.get("isPrivate") else "🌍 Public"
    stars = repo.get("stargazerCount", 0)
    lang = repo.get("primaryLanguage")
    language_badge = f" • 💻 {lang['name']}" if lang else ""
    repo_url = repo.get("url", "#")
    name = repo.get("name", "Unknown")

    md = f"#### 📁 [{name}]({repo_url})\n"
    md += f"> {visibility_badge} • ⭐ {stars} Stars{language_badge}\n\n"

    # Commits formatting
    commits = []
    default_branch = repo.get("defaultBranchRef")
    if default_branch and default_branch.get("target") and default_branch["target"].get("history"):
        commits = default_branch["target"]["history"].get("nodes", [])

    if commits:
        md += "📝 **Derniers Commits :**\n"
        for commit in commits:
            date_str = commit.get("committedDate")
            msg = commit.get("messageHeadline", "No message")
            if date_str:
                # Convert ISO date to readable format
                dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                formatted_date = dt.strftime("%d %b %Y")
                md += f"- `{formatted_date}` : {msg}\n"
            else:
                md += f"- {msg}\n"
    else:
        md += "📝 *Aucun commit récent trouvé.*\n"

    md += "\n"
    return md

def update_readme(markdown_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    # Regex to find the dynamic section
    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # Substitution using lambda to avoid regex group issues with commit messages
    updated_readme = re.sub(
        pattern,
        lambda m: f"{m.group(1)}{markdown_content}\n{m.group(2)}",
        readme,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)
    print("README.md updated successfully!")

if __name__ == "__main__":
    repos = fetch_repositories()
    if not repos:
        print("No repositories found or failed to fetch.")
        exit(0)

    full_markdown = ""
    for repo in repos:
        full_markdown += format_repo_markdown(repo)

    update_readme(full_markdown.strip())
