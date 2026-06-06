import os
import requests
import re

USERNAME = "LaTortu3"
TOKEN = os.getenv("GH_TOKEN")

# Fallback mock data in case GH_TOKEN is not available
MOCK_DATA = """
- **[repo-mock-1](https://github.com/LaTortu3/repo-mock-1)** (Public) - ⭐️ 5 | Python
  - *feat: mock feature 1*
  - *fix: mock bug 1*
  - *docs: mock docs 1*
- **[repo-mock-2](https://github.com/LaTortu3/repo-mock-2)** (Private) - ⭐️ 2 | JavaScript
  - *feat: mock feature 2*
  - *refactor: mock refactor*
"""

def fetch_repos():
    if not TOKEN:
        print("No GH_TOKEN found, using mock data.")
        return MOCK_DATA.strip()

    query = """
    {
      user(login: "%s") {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
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
                    nodes {
                      messageHeadline
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

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
        response.raise_for_status()
        data = response.json()

        repos = data.get('data', {}).get('user', {}).get('repositories', {}).get('nodes', [])

        if not repos:
            return "Aucun dépôt trouvé."

        repo_markdown = ""
        for repo in repos:
            name = repo['name']
            url = repo['url']
            visibility = "Private" if repo['isPrivate'] else "Public"
            stars = repo['stargazerCount']
            lang = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "N/A"

            repo_markdown += f"- **[{name}]({url})** ({visibility}) - ⭐️ {stars} | {lang}\n"

            commits = []
            if repo.get('defaultBranchRef') and repo['defaultBranchRef'].get('target'):
                commits = repo['defaultBranchRef']['target']['history']['nodes']

            for commit in commits:
                msg = commit['messageHeadline']
                repo_markdown += f"  - *{msg}*\n"

        return repo_markdown.strip()

    except Exception as e:
        print(f"Error fetching data: {e}")
        return MOCK_DATA.strip()

def update_readme(repo_data):
    try:
        with open("README.md", "r", encoding="utf-8") as file:
            readme_content = file.read()

        start_marker = "<!-- DYNAMIC_REPOS_START -->"
        end_marker = "<!-- DYNAMIC_REPOS_END -->"

        # Regex to find the content between markers
        pattern = f"{start_marker}.*?{end_marker}"
        replacement = f"{start_marker}\n{repo_data}\n{end_marker}"

        new_content = re.sub(pattern, replacement, readme_content, flags=re.DOTALL)

        with open("README.md", "w", encoding="utf-8") as file:
            file.write(new_content)

        print("README.md updated successfully.")

    except Exception as e:
        print(f"Error updating README.md: {e}")

if __name__ == "__main__":
    markdown_data = fetch_repos()
    update_readme(markdown_data)
