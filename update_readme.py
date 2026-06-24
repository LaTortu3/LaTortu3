import os
import re
import requests
import datetime

# GitHub GraphQL API Endpoint
GRAPHQL_URL = "https://api.github.com/graphql"

# GraphQL Query to fetch repos (up to 100, ordered by pushed date), their visibility, stars, language, and last 3 commits
GRAPHQL_QUERY = """
query {
  viewer {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, isFork: false) {
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

def fetch_github_data(token):
    headers = {
        "Authorization": f"bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(GRAPHQL_URL, json={"query": GRAPHQL_QUERY}, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

    return response.json()

def format_date(date_string):
    # Parses GitHub ISO 8601 string and returns formatted date
    dt = datetime.datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    return dt.strftime("%d/%m/%Y")

def generate_markdown(data):
    markdown = ""
    repos = data.get("data", {}).get("viewer", {}).get("repositories", {}).get("nodes", [])

    if not repos:
        return "Aucun dépôt trouvé ou erreur lors de la récupération.\n"

    for repo in repos:
        name = repo.get("name")
        url = repo.get("url")
        visibility = repo.get("visibility")
        stars = repo.get("stargazerCount", 0)

        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name") if lang_node else "N/A"

        # Badge generation
        visibility_badge = "🟢 Public" if visibility == "PUBLIC" else "🔴 Privé"
        stars_badge = f"⭐ {stars}"

        markdown += f"#### 📁 [{name}]({url})\n"
        markdown += f"**Visibilité:** {visibility_badge} | **Langage Principal:** `{lang}` | **Stars:** {stars_badge}\n\n"

        # Fetching commits
        markdown += "📝 **Derniers Commits :**\n"
        default_branch = repo.get("defaultBranchRef")
        if default_branch:
            target = default_branch.get("target")
            if target and target.get("history"):
                edges = target.get("history").get("edges", [])
                if edges:
                    for edge in edges:
                        commit = edge.get("node")
                        if commit:
                            msg = commit.get("messageHeadline")
                            date = format_date(commit.get("committedDate"))
                            markdown += f"- `{date}` : {msg}\n"
                else:
                    markdown += "- *Aucun commit récent trouvé.*\n"
            else:
                 markdown += "- *Aucun historique de commit.*\n"
        else:
             markdown += "- *Branche par défaut non trouvée (dépôt potentiellement vide).*\n"

        markdown += "\n---\n\n"

    return markdown

def get_mock_markdown():
    return """
#### 📁 [mock-repo-1](https://github.com/LaTortu3/mock-repo-1)
**Visibilité:** 🟢 Public | **Langage Principal:** `Python` | **Stars:** ⭐ 42

📝 **Derniers Commits :**
- `01/04/2026` : Initial commit
- `02/04/2026` : Add feature X
- `03/04/2026` : Fix bug Y

---

#### 📁 [mock-repo-2](https://github.com/LaTortu3/mock-repo-2)
**Visibilité:** 🔴 Privé | **Langage Principal:** `JavaScript` | **Stars:** ⭐ 5

📝 **Derniers Commits :**
- `01/04/2026` : Setup React project

---
"""

def update_readme(new_content):
    readme_path = "README.md"

    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # The regex looks for the START and END tags and captures everything in between.
    # re.DOTALL ensures the '.' matches newlines as well.
    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    # We use a lambda to avoid backreference parsing issues with the replacement string.
    new_readme_content = re.sub(
        pattern,
        lambda m: f"{m.group(1)}{new_content}{m.group(2)}",
        readme_content,
        flags=re.DOTALL
    )

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_readme_content)

def main():
    token = os.environ.get("GH_TOKEN")
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
             raise ValueError("GH_TOKEN is missing but running in GitHub Actions context! Refusing to use mock data in production.")
        else:
             print("GH_TOKEN not found. Using mock data for local testing.")
             markdown_content = get_mock_markdown()
    else:
        print("GH_TOKEN found. Fetching data from GitHub...")
        try:
            data = fetch_github_data(token)
            markdown_content = generate_markdown(data)
        except Exception as e:
            print(f"Error fetching data: {e}")
            if is_github_actions:
                 raise e
            else:
                 print("Falling back to mock data due to API error.")
                 markdown_content = get_mock_markdown()

    update_readme(markdown_content)
    print("README.md updated successfully.")

if __name__ == "__main__":
    main()
