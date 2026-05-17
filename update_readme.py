import os
import requests
import re
from datetime import datetime

GITHUB_USERNAME = "LaTortu3"
GITHUB_TOKEN = os.getenv("GH_TOKEN")
GRAPHQL_URL = "https://api.github.com/graphql"

def get_repos():
    if not GITHUB_TOKEN:
        print("Warning: GH_TOKEN not found. Returning empty repo list for local testing.")
        return []

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    # Fetch 100 repositories
    query = """
    {
      user(login: "LaTortu3") {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
          nodes {
            name
            description
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
                      pushedDate
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

    response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print(f"GraphQL Errors: {data['errors']}")
            return []
        return data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
    else:
        print(f"Failed to fetch repositories: {response.status_code} - {response.text}")
        return []

def generate_markdown(repos):
    if not repos:
        return "<p><em>Aucune donnée dynamique à afficher (token manquant ou aucune repo).</em></p>\n"

    markdown = ""
    for repo in repos:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        is_private = repo.get("isPrivate", False)
        stars = repo.get("stargazerCount", 0)
        desc = repo.get("description") or "Aucune description fournie."
        lang = repo.get("primaryLanguage")
        lang_name = lang.get("name") if lang else "Non spécifié"

        visibility = "🔒 Privé" if is_private else "🌍 Public"

        markdown += f"#### [{name}]({url}) - {visibility}\n"
        markdown += f"**Description:** {desc}\n\n"
        markdown += f"**Langage Principal:** `{lang_name}` | ⭐ **Stars:** {stars}\n\n"

        default_branch = repo.get("defaultBranchRef")
        if default_branch:
            target = default_branch.get("target", {})
            history = target.get("history", {}).get("nodes", [])
            if history:
                markdown += "**Derniers Commits & Avancements:**\n"
                for commit in history:
                    msg = commit.get("messageHeadline", "")
                    date_str = commit.get("pushedDate", "")
                    if date_str:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                        formatted_date = date_obj.strftime("%d/%m/%Y")
                        markdown += f"- *{formatted_date}* : {msg}\n"
                markdown += "\n"

        markdown += "---\n\n"

    return markdown

def update_readme(markdown_content):
    readme_path = "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Regular expression to find the block between the comments
        pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

        # Check if markers exist
        if not re.search(pattern, content, flags=re.DOTALL):
            print("Error: Could not find DYNAMIC_REPOS_START and DYNAMIC_REPOS_END markers in README.md")
            return

        replacement = rf"\1\n{markdown_content}\n\2"
        updated_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated_content)

        print("README.md updated successfully.")
    except Exception as e:
        print(f"An error occurred while updating README.md: {e}")

if __name__ == "__main__":
    print("Fetching repos...")
    repos = get_repos()
    print(f"Found {len(repos)} repositories.")
    markdown = generate_markdown(repos)
    update_readme(markdown)
