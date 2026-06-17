import os
import requests
import re
from datetime import datetime

# GitHub GraphQL API endpoint
API_URL = "https://api.github.com/graphql"

# Try to get the token from the environment
TOKEN = os.getenv("GH_TOKEN")
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

def get_repos_mock_data():
    return [
        {
            "name": "mock-repo-1",
            "url": "https://github.com/LaTortu3/mock-repo-1",
            "visibility": "PUBLIC",
            "stargazerCount": 5,
            "primaryLanguage": "Python",
            "commits": [
                {"message": "Initial commit", "date": "2023-01-01T10:00:00Z"},
                {"message": "Add feature X", "date": "2023-01-05T12:30:00Z"},
            ]
        },
        {
            "name": "private-game-project",
            "url": "https://github.com/LaTortu3/private-game-project",
            "visibility": "PRIVATE",
            "stargazerCount": 2,
            "primaryLanguage": "C++",
            "commits": [
                {"message": "Setup Unreal Engine", "date": "2023-02-10T09:15:00Z"},
                {"message": "Implement Lua scripting", "date": "2023-02-15T16:45:00Z"},
                {"message": "Fix rendering bug", "date": "2023-02-20T11:20:00Z"}
            ]
        }
    ]

def fetch_repos():
    if not TOKEN:
        if IS_GITHUB_ACTIONS:
            raise ValueError("GH_TOKEN environment variable is required in GitHub Actions.")
        else:
            print("Warning: GH_TOKEN not found. Using mock data for local testing.")
            return get_repos_mock_data()

    headers = {"Authorization": f"Bearer {TOKEN}"}

    query = """
    {
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

    response = requests.post(API_URL, json={'query': query}, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

    data = response.json()
    if 'errors' in data:
         raise Exception(f"GraphQL errors: {data['errors']}")

    repos = []
    for node in data['data']['viewer']['repositories']['nodes']:
        commits = []
        if node.get('defaultBranchRef') and node['defaultBranchRef'].get('target'):
            for commit in node['defaultBranchRef']['target']['history']['nodes']:
                commits.append({
                    "message": commit['messageHeadline'],
                    "date": commit['committedDate']
                })

        repos.append({
            "name": node['name'],
            "url": node['url'],
            "visibility": node['visibility'],
            "stargazerCount": node['stargazerCount'],
            "primaryLanguage": node['primaryLanguage']['name'] if node.get('primaryLanguage') else 'Unknown',
            "commits": commits
        })

    return repos

def format_date(iso_date):
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return iso_date

def generate_markdown(repos):
    md = ""
    for repo in repos:
        icon = "🔒" if repo['visibility'] == "PRIVATE" else "🌍"
        stars = f"⭐ {repo['stargazerCount']}" if repo['stargazerCount'] > 0 else ""
        lang = f"| 💻 {repo['primaryLanguage']}" if repo['primaryLanguage'] != 'Unknown' else ""

        md += f"#### [{icon} {repo['name']}]({repo['url']}) {stars} {lang}\n"

        if repo['commits']:
            md += "Derniers commits :\n"
            for commit in repo['commits']:
                date_str = format_date(commit['date'])
                # Escape markdown special characters in message just in case
                msg = commit['message'].replace('*', '\\*').replace('_', '\\_')
                md += f"- `{date_str}` : {msg}\n"
        else:
            md += "- *Aucun commit récent*\n"
        md += "\n"
    return md

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Define the tags
    start_tag = "<!-- DYNAMIC_REPOS_START -->"
    end_tag = "<!-- DYNAMIC_REPOS_END -->"

    # Regex to find the content between the tags
    pattern = re.compile(rf"({start_tag}).*?({end_tag})", re.DOTALL)

    if not pattern.search(readme_content):
        print("Warning: Tags not found in README.md")
        return

    # Replace the old content with the new content using lambda to avoid backreference parsing errors
    updated_readme = pattern.sub(lambda m: f"{m.group(1)}\n{new_content}{m.group(2)}", readme_content)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print("README.md updated successfully!")

if __name__ == "__main__":
    repos = fetch_repos()
    markdown_content = generate_markdown(repos)
    update_readme(markdown_content)
