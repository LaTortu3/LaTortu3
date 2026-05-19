import os
import requests
import re

# Use GH_TOKEN if available (Action context), fallback to GITHUB_TOKEN if testing locally
TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")
USERNAME = "LaTortu3"

def fetch_repos():
    if not TOKEN:
        print("Warning: No GH_TOKEN or GITHUB_TOKEN environment variable found. Unable to fetch real data.")
        return []

    headers = {"Authorization": f"Bearer {TOKEN}"}
    query = """
    {
      user(login: "%s") {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
          nodes {
            name
            url
            isPrivate
            stargazerCount
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 3) {
                    totalCount
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

    response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['user']['repositories']['nodes']
    else:
        print(f"Query failed to run by returning code of {response.status_code}. {response.text}")
        return []

def generate_markdown(repos):
    if not repos:
        return "*(Aucune donnée de dépôt trouvée ou token manquant)*\n"

    md = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        stars = repo['stargazerCount']
        is_private = repo['isPrivate']

        visibility = "🔒 Privé" if is_private else "🌐 Public"
        md += f"#### [{name}]({url}) ({visibility})\n"
        md += f"⭐ **Stars:** {stars}\n"

        default_branch = repo.get('defaultBranchRef')
        if default_branch and default_branch.get('target'):
            history = default_branch['target'].get('history')
            if history:
                total_commits = history.get('totalCount', 0)
                md += f"📈 **Commits Totaux:** {total_commits}\n"

                commits = history.get('nodes', [])
                if commits:
                    md += "🔄 **Derniers Commits:**\n"
                    for commit in commits:
                        msg = commit.get('messageHeadline', '').strip()
                        if msg:
                            md += f"- {msg}\n"
        md += "\n"
    return md

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    # The markers
    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    pattern = re.compile(rf"{start_marker}.*?{end_marker}", re.DOTALL)

    replacement = f"{start_marker}\n{new_content}\n{end_marker}"

    updated_readme = re.sub(pattern, replacement, readme)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print("README.md updated successfully.")

if __name__ == "__main__":
    repos = fetch_repos()
    md_content = generate_markdown(repos)
    update_readme(md_content)
