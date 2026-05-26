import os
import requests
import re

GITHUB_USERNAME = "LaTortu3"
GRAPHQL_URL = "https://api.github.com/graphql"

def get_repos_mock():
    return [
        {
            "name": "Awesome-Unreal-Lua",
            "stargazers": 42,
            "primary_language": "Lua",
            "commits": [
                {"message": "Add new enemy logic", "date": "2023-10-25"},
                {"message": "Fix UI bug", "date": "2023-10-24"},
                {"message": "Initial commit", "date": "2023-10-23"}
            ]
        },
        {
            "name": "React-Portfolio",
            "stargazers": 15,
            "primary_language": "JavaScript",
            "commits": [
                {"message": "Update about section", "date": "2023-10-26"},
                {"message": "Add dynamic routing", "date": "2023-10-20"},
                {"message": "Fix mobile layout", "date": "2023-10-18"}
            ]
        },
        {
            "name": "Python-Automation-Scripts",
            "stargazers": 8,
            "primary_language": "Python",
            "commits": [
                {"message": "Refactor API client", "date": "2023-10-27"},
                {"message": "Add retry logic", "date": "2023-10-22"},
                {"message": "Setup project", "date": "2023-10-15"}
            ]
        }
    ]

def fetch_repos(token):
    query = """
    {
      user(login: "%s") {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
          nodes {
            name
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
    """ % GITHUB_USERNAME

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code}")
        return []

    data = response.json()
    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        return []

    repos_data = data.get('data', {}).get('user', {}).get('repositories', {}).get('nodes', [])

    formatted_repos = []
    for repo in repos_data:
        name = repo.get('name', 'Unknown')
        stars = repo.get('stargazerCount', 0)
        lang_node = repo.get('primaryLanguage')
        lang = lang_node.get('name') if lang_node else "N/A"

        commits = []
        default_branch = repo.get('defaultBranchRef')
        if default_branch:
            target = default_branch.get('target', {})
            history = target.get('history', {}).get('edges', [])
            for edge in history:
                node = edge.get('node', {})
                commits.append({
                    "message": node.get('messageHeadline', ''),
                    "date": node.get('committedDate', '')[:10] # Just the date
                })

        formatted_repos.append({
            "name": name,
            "stargazers": stars,
            "primary_language": lang,
            "commits": commits
        })

    return formatted_repos

def format_repo_markdown(repos):
    if not repos:
        return "No repositories found."

    md = ""
    for repo in repos:
        md += f"#### 📁 [{repo['name']}](https://github.com/{GITHUB_USERNAME}/{repo['name']}) 🌟 {repo['stargazers']} | 🛠 {repo['primary_language']}\n"
        md += "📝 **Derniers Commits :**\n"
        if not repo['commits']:
            md += "- _Aucun commit récent_\n"
        else:
            for commit in repo['commits']:
                md += f"- `{commit['date']}` : {commit['message']}\n"
        md += "\n"
    return md

def update_readme(markdown_content):
    readme_path = "README.md"

    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: {readme_path} not found.")
        return

    # Replace content between markers
    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"
    replacement = f"\\1\n{markdown_content}\n\\2"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("README.md successfully updated!")

def main():
    token = os.environ.get("GH_TOKEN")

    if token:
        print("GH_TOKEN found. Fetching real data from GitHub API...")
        repos = fetch_repos(token)
    else:
        print("GH_TOKEN not found. Using mock data for local testing...")
        repos = get_repos_mock()

    markdown_content = format_repo_markdown(repos)
    update_readme(markdown_content)

if __name__ == "__main__":
    main()
