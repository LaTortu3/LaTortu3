import os
import requests

GITHUB_USERNAME = "LaTortu3"
GITHUB_TOKEN = os.getenv("GH_TOKEN")

if not GITHUB_TOKEN:
    print("WARNING: GH_TOKEN not set. Running without authentication which might limit API limits and private repos access.")

def fetch_repos():
    # Use GraphQL API to get public and private repos, stars, and recent commits
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

    query = """
    query {
      user(login: "%s") {
        repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            isPrivate
            stargazerCount
            description
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
    """ % GITHUB_USERNAME

    response = requests.post(url, json={'query': query}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print("GraphQL Errors:", data['errors'])
            return []
        if 'data' in data and data['data']['user']:
            return data['data']['user']['repositories']['nodes']
    else:
        print(f"Failed to fetch repositories. Status code: {response.status_code}")
        print(response.text)
    return []

def generate_markdown(repos):
    markdown = "### 📚 My Projects & Repositories\n\n"
    markdown += "*(Dynamically generated lists of my public and private work)*\n\n"

    for repo in repos:
        name = repo['name']
        url = repo['url']
        stars = repo['stargazerCount']
        desc = repo.get('description') or "No description provided."
        lang = repo.get('primaryLanguage')
        lang_name = lang['name'] if lang else "Unknown"
        is_private = "🔒 Private" if repo['isPrivate'] else "🌍 Public"

        markdown += f"#### [{name}]({url}) ({is_private})\n"
        markdown += f"**{lang_name}** | ⭐ {stars} stars\n\n"
        markdown += f"> {desc}\n\n"

        # Add commits
        commits = []
        if repo.get('defaultBranchRef') and repo['defaultBranchRef'].get('target'):
             commits = repo['defaultBranchRef']['target']['history']['nodes']

        if commits:
            markdown += "**Recent Commits:**\n"
            for commit in commits:
                msg = commit['messageHeadline']
                markdown += f"- `{msg}`\n"
        else:
            markdown += "*No recent commits found.*\n"

        markdown += "\n---\n"

    return markdown

def update_readme(new_content):
    with open("README.md", "r") as f:
        readme_content = f.read()

    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    start_idx = readme_content.find(start_marker)
    end_idx = readme_content.find(end_marker)

    if start_idx != -1 and end_idx != -1:
        updated_readme = (
            readme_content[:start_idx + len(start_marker)] +
            "\n\n" + new_content + "\n" +
            readme_content[end_idx:]
        )
        with open("README.md", "w") as f:
            f.write(updated_readme)
        print("README.md updated successfully!")
    else:
        print("Markers not found in README.md. Please add <!-- DYNAMIC_REPOS_START --> and <!-- DYNAMIC_REPOS_END -->.")

if __name__ == "__main__":
    repos = fetch_repos()
    if repos:
        md_content = generate_markdown(repos)
        update_readme(md_content)
    else:
        print("No repos fetched or an error occurred.")
