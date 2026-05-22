import os
import requests
import json
from datetime import datetime

# Retrieve token and set headers
GITHUB_TOKEN = os.getenv("GH_TOKEN")
if not GITHUB_TOKEN:
    print("WARNING: GH_TOKEN environment variable not set. Using mock data.")
    GITHUB_TOKEN = "MOCK_TOKEN"

USERNAME = "LaTortu3"
HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# The GraphQL query to fetch public and private repos (up to 100)
# We fetch name, description, stargazers count, and the last 3 commits from the default branch.
GRAPHQL_QUERY = """
{
  user(login: "LaTortu3") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
      nodes {
        name
        description
        url
        stargazerCount
        isPrivate
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

def fetch_repos():
    if GITHUB_TOKEN == "MOCK_TOKEN":
        # Return empty list or mock data
        return []

    url = "https://api.github.com/graphql"
    payload = {"query": GRAPHQL_QUERY}
    response = requests.post(url, headers=HEADERS, json=payload)

    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("Errors returned from GraphQL API:", data["errors"])
            return []

        try:
            repos = data["data"]["user"]["repositories"]["nodes"]
            return repos
        except KeyError as e:
            print(f"Error parsing response data: {e}")
            return []
    else:
        print(f"Query failed with status code {response.status_code}")
        print(response.text)
        return []

def generate_markdown(repos):
    if not repos:
        return "*(Aucune donnée de repository disponible pour le moment)*\n"

    md = "### 📦 Mes Projets Récents\n\n"

    # Sort repos by some criteria if necessary, they are already sorted by PUSHED_AT DESC by the query
    for repo in repos:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        description = repo.get("description") or "Aucune description fournie."
        stars = repo.get("stargazerCount", 0)
        is_private = repo.get("isPrivate", False)

        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name", "N/A") if lang_node else "N/A"

        private_badge = "🔒 Private" if is_private else "🌍 Public"

        md += f"#### [{name}]({url}) - ⭐ {stars} | {private_badge} | 🗣️ {lang}\n"
        md += f"> {description}\n\n"

        # Commits
        default_branch = repo.get("defaultBranchRef")
        if default_branch and default_branch.get("target") and default_branch["target"].get("history"):
            commits = default_branch["target"]["history"].get("nodes", [])
            if commits:
                md += "**Derniers Commits :**\n"
                for commit in commits:
                    msg = commit.get("messageHeadline", "")
                    date_str = commit.get("committedDate", "")
                    oid = commit.get("oid", "")[:7]

                    if date_str:
                        date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
                        date_formatted = date_obj.strftime("%d %b %Y")
                    else:
                        date_formatted = "Unknown date"

                    md += f"- `{oid}` ({date_formatted}): {msg}\n"
            else:
                md += "- *Aucun commit récent trouvé.*\n"
        else:
            md += "- *Aucun historique de commit disponible.*\n"

        md += "\n---\n"

    return md

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Define markers
    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    if start_marker in readme_content and end_marker in readme_content:
        # Replace content between markers
        start_index = readme_content.find(start_marker) + len(start_marker)
        end_index = readme_content.find(end_marker)

        updated_readme = (
            readme_content[:start_index]
            + "\n" + new_content + "\n"
            + readme_content[end_index:]
        )
    else:
        print("Markers not found in README.md. Cannot inject dynamic content.")
        # Alternatively, append it if markers are missing
        # This is a fallback behavior
        updated_readme = readme_content

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)
    print("README.md updated successfully.")

if __name__ == "__main__":
    repos = fetch_repos()
    md_content = generate_markdown(repos)
    update_readme(md_content)
