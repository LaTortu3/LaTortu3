import os
import requests
import re
from datetime import datetime

# GitHub GraphQL API endpoint
API_URL = "https://api.github.com/graphql"

# GraphQL Query to fetch repositories and their latest commits
QUERY = """
query {
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
"""

# Mock data for local testing without token
MOCK_DATA = [
    {
        "name": "Super-Secret-Project",
        "url": "https://github.com/LaTortu3/Super-Secret-Project",
        "visibility": "PRIVATE",
        "stargazerCount": 42,
        "primaryLanguage": {"name": "Python"},
        "commits": [
            {"messageHeadline": "Initial commit for the secret weapon", "committedDate": "2026-04-01T12:00:00Z"},
            {"messageHeadline": "Add more stealth", "committedDate": "2026-04-02T15:30:00Z"}
        ]
    },
    {
        "name": "Awesome-Unreal-Game",
        "url": "https://github.com/LaTortu3/Awesome-Unreal-Game",
        "visibility": "PUBLIC",
        "stargazerCount": 1337,
        "primaryLanguage": {"name": "C++"},
        "commits": [
            {"messageHeadline": "Fix rendering bug", "committedDate": "2026-03-25T10:15:00Z"},
            {"messageHeadline": "Implement new Lua scripting API", "committedDate": "2026-03-20T09:00:00Z"},
            {"messageHeadline": "Update textures", "committedDate": "2026-03-18T14:20:00Z"}
        ]
    }
]

def fetch_repos_data(token):
    """Fetches repository data using the GitHub GraphQL API."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(API_URL, json={"query": QUERY}, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("GraphQL Errors:", data["errors"])
            raise Exception("GraphQL query failed with errors.")
        return data["data"]["viewer"]["repositories"]["nodes"]
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def format_date(date_str):
    """Formats a ISO 8601 date string to a more readable format."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except ValueError:
        return date_str

def generate_markdown(repos):
    """Generates the Markdown string for the repositories."""
    md_content = ""
    for repo in repos:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        visibility = repo.get("visibility", "PUBLIC")
        stars = repo.get("stargazerCount", 0)

        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name", "Unknown") if lang_node else "Unknown"

        vis_emoji = "🔒" if visibility == "PRIVATE" else "🌍"

        md_content += f"#### [{name}]({url}) {vis_emoji}\n"
        md_content += f"- **Langage principal :** {lang} | **Étoiles :** {stars} ⭐\n"
        md_content += f"- **Derniers commits :**\n"

        # Handle both real API structure and mock data structure
        commits = []
        if "commits" in repo:
            commits = repo["commits"]
        else:
            try:
                commits = repo["defaultBranchRef"]["target"]["history"]["nodes"]
            except (KeyError, TypeError):
                commits = []

        if commits:
            for commit in commits:
                msg = commit.get("messageHeadline", "Sans message")
                date = format_date(commit.get("committedDate", ""))
                md_content += f"  - `{date}` : {msg}\n"
        else:
            md_content += "  - *Aucun commit récent ou historique inaccessible*\n"

        md_content += "\n"

    return md_content

def update_readme(new_content, filepath="README.md"):
    """Updates the README.md file with the new content between the markers."""
    with open(filepath, "r", encoding="utf-8") as file:
        readme_content = file.read()

    # Regex to find the markers and everything in between
    # Using re.DOTALL to match newlines as well
    pattern = r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)'

    # Use a lambda to avoid backreference issues with \n or \g in the replacement string
    updated_readme = re.sub(
        pattern,
        lambda m: f'{m.group(1)}{new_content}{m.group(2)}',
        readme_content,
        flags=re.DOTALL
    )

    with open(filepath, "w", encoding="utf-8") as file:
        file.write(updated_readme)

    print("README.md updated successfully.")

def main():
    token = os.environ.get("GH_TOKEN")
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise ValueError("GH_TOKEN environment variable is missing in GitHub Actions environment. Aborting.")
        else:
            print("GH_TOKEN not found. Using mock data for local testing.")
            repos_data = MOCK_DATA
    else:
        print("Fetching data from GitHub API...")
        repos_data = fetch_repos_data(token)

    # Generate markdown content
    print("Generating Markdown...")
    new_markdown = generate_markdown(repos_data)

    # Update README
    print("Updating README.md...")
    update_readme(new_markdown)

if __name__ == "__main__":
    main()
