import os
import requests
import re

GITHUB_TOKEN = os.getenv("GH_TOKEN")
USERNAME = "LaTortu3"
README_PATH = "README.md"

def fetch_repositories():
    if not GITHUB_TOKEN:
        print("Warning: GH_TOKEN not found. Using empty data for testing if no token.")
        # Return mock data if no token for testing
        return []

    headers = {
        "Authorization": f"bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    query {
      user(login: "%s") {
        repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes {
            name
            url
            description
            stargazerCount
            isPrivate
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
    """ % USERNAME

    try:
        response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print(f"GraphQL Errors: {data['errors']}")
            return []

        repos = data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
        return repos
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def format_repositories(repos):
    if not repos:
        return "<!-- Aucune donnée de dépôt trouvée ou erreur lors de la récupération. -->\n"

    markdown = ""
    for idx, repo in enumerate(repos, 1):
        name = repo.get('name')
        url = repo.get('url')
        desc = repo.get('description') or "Pas de description"
        stars = repo.get('stargazerCount', 0)
        is_private = repo.get('isPrivate', False)
        lang = repo.get('primaryLanguage', {}).get('name') if repo.get('primaryLanguage') else "N/A"

        private_badge = "🔒 Privé" if is_private else "🌍 Public"

        markdown += f"### {idx}. [{name}]({url}) - {private_badge} | ⭐️ {stars} | 💻 {lang}\n"
        markdown += f"> {desc}\n\n"

        # Commits
        branch_ref = repo.get('defaultBranchRef')
        if branch_ref:
            history = branch_ref.get('target', {}).get('history', {}).get('edges', [])
            if history:
                markdown += "**Derniers commits :**\n"
                for edge in history:
                    commit = edge.get('node', {})
                    msg = commit.get('messageHeadline', 'Sans message')
                    date = commit.get('committedDate', '').split('T')[0]
                    markdown += f"- `{date}` : {msg}\n"
        markdown += "\n---\n"

    return markdown

def update_readme(new_content):
    try:
        with open(README_PATH, 'r', encoding='utf-8') as f:
            content = f.read()

        start_marker = "<!-- DYNAMIC_REPOS_START -->\n"
        end_marker = "<!-- DYNAMIC_REPOS_END -->"

        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)

        if start_idx == -1 or end_idx == -1 or start_idx >= end_idx:
            print("Error: Markers not found or incorrectly placed in README.md")
            return False

        updated_content = (
            content[:start_idx + len(start_marker)] +
            new_content +
            content[end_idx:]
        )

        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(updated_content)

        print("README.md successfully updated!")
        return True
    except FileNotFoundError:
        print(f"Error: {README_PATH} not found.")
        return False

if __name__ == "__main__":
    print("Fetching repositories...")
    repos = fetch_repositories()
    print(f"Fetched {len(repos)} repositories.")

    print("Formatting content...")
    formatted_content = format_repositories(repos)

    print("Updating README...")
    update_readme(formatted_content)
