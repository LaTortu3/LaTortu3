import os
import requests
import re
from datetime import datetime

GITHUB_USERNAME = "LaTortu3"
GH_TOKEN = os.environ.get("GH_TOKEN")

GRAPHQL_QUERY = """
query {
  user(login: "%s") {
    repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        description
        url
        isPrivate
        stargazerCount
        languages(first: 5, orderBy: {field: SIZE, direction: DESC}) {
          nodes {
            name
          }
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 3) {
                nodes {
                  message
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

def process_data(data):
    if not data or 'data' not in data or 'user' not in data['data'] or 'repositories' not in data['data']['user']:
        return "<!-- No data available -->"

    repos = data['data']['user']['repositories']['nodes']

    if not repos:
        return "<!-- No repositories found -->"

    markdown_content = "### 📚 My Dynamic Repository Showcase\n\n"
    markdown_content += "<details>\n<summary>Click to view my latest work and stats</summary>\n\n"

    for repo in repos:
        name = repo.get('name', 'Unknown')
        url = repo.get('url', '#')
        description = repo.get('description') or "No description provided."
        is_private = repo.get('isPrivate', False)
        visibility = "🔒 Private" if is_private else "🌐 Public"
        stars = repo.get('stargazerCount', 0)

        # Format languages
        languages = []
        if 'languages' in repo and repo['languages'] and 'nodes' in repo['languages']:
            languages = [lang['name'] for lang in repo['languages']['nodes']]
        lang_str = ", ".join(languages) if languages else "Not specified"

        markdown_content += f"#### [{name}]({url}) {visibility} | ⭐️ {stars}\n"
        markdown_content += f"**Description**: {description}\n\n"
        markdown_content += f"**Tech Stack**: {lang_str}\n\n"

        # Skill and integration comments based on languages
        skills = []
        if "Python" in languages:
            skills.append("Python for scripting, backend logic, and automation.")
        if "JavaScript" in languages or "TypeScript" in languages:
            skills.append("JavaScript/TypeScript for dynamic frontend and server-side operations.")
        if "HTML" in languages or "CSS" in languages:
            skills.append("Solid web fundamentals for UI structuring and styling.")
        if "Lua" in languages:
            skills.append("Lua for game development scripting (Unreal Engine).")

        if skills:
            markdown_content += f"**Skill Highlights**: {' '.join(skills)}\n\n"

        # Recent commits
        commits_md = ""
        try:
            commits = repo['defaultBranchRef']['target']['history']['nodes']
            if commits:
                commits_md += "**Recent Commits**:\n"
                for commit in commits:
                    msg = commit.get('message', '').split('\n')[0] # Get first line of commit message
                    commits_md += f"- `{msg}`\n"
        except (KeyError, TypeError):
            commits_md = "- *No recent commits available*\n"

        markdown_content += commits_md + "\n---\n\n"

    markdown_content += "</details>\n"
    return markdown_content

def fetch_github_data():
    if not GH_TOKEN:
        print("Warning: GH_TOKEN is not set. Data fetching will be skipped or may fail.")
        return None

    headers = {
        "Authorization": f"bearer {GH_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": GRAPHQL_QUERY},
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from GitHub: {e}")
        return None

def update_readme(content):
    readme_path = "README.md"
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme_text = f.read()

        # Define the markers
        start_marker = "<!-- DYNAMIC_REPOS_START -->"
        end_marker = "<!-- DYNAMIC_REPOS_END -->"

        # Use regex to replace the content between markers
        pattern = re.compile(f"({start_marker}).*?({end_marker})", re.DOTALL)

        if not pattern.search(readme_text):
            print("Error: Markers not found in README.md")
            return False

        new_readme_text = pattern.sub(rf"\1\n{content}\n\2", readme_text)

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme_text)

        print("README.md updated successfully.")
        return True
    except Exception as e:
        print(f"Error updating README.md: {e}")
        return False

if __name__ == "__main__":
    data = fetch_github_data()
    if data:
        content = process_data(data)
        update_readme(content)
        print("Process completed.")
