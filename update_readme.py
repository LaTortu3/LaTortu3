import os
import requests
import re
from datetime import datetime

GITHUB_USERNAME = "LaTortu3"
TOKEN = os.environ.get("GH_TOKEN")

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
{
  user(login: "%s") {
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

def fetch_repos_graphql():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    try:
        response = requests.post(GRAPHQL_URL, json={'query': QUERY}, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'errors' in data:
            print("GraphQL Errors:", data['errors'])
            return None
        return data['data']['user']['repositories']['nodes']
    except Exception as e:
        print(f"Error fetching data via GraphQL: {e}")
        return None

def get_mock_repos():
    return [
        {
            "name": "unreal-project-alpha",
            "url": "https://github.com/LaTortu3/unreal-project-alpha",
            "visibility": "PUBLIC",
            "stargazerCount": 42,
            "primaryLanguage": {"name": "C++"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Implemented new combat mechanics"}},
                            {"node": {"messageHeadline": "Fixed memory leak in level 3"}},
                            {"node": {"messageHeadline": "Updated UE version to 5.3"}}
                        ]
                    }
                }
            }
        },
        {
            "name": "lua-scripts",
            "url": "https://github.com/LaTortu3/lua-scripts",
            "visibility": "PRIVATE",
            "stargazerCount": 5,
            "primaryLanguage": {"name": "Lua"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Add AI behavior script"}},
                            {"node": {"messageHeadline": "Refactor event system"}},
                        ]
                    }
                }
            }
        },
        {
            "name": "github-profile-readme",
            "url": "https://github.com/LaTortu3/github-profile-readme",
            "visibility": "PUBLIC",
            "stargazerCount": 10,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Update README.md with dynamic data"}},
                        ]
                    }
                }
            }
        }
    ]

def generate_markdown(repos):
    if not repos:
        return "<!-- DYNAMIC_REPOS_START -->\n_Aucun dépôt trouvé._\n<!-- DYNAMIC_REPOS_END -->"

    md_content = "<!-- DYNAMIC_REPOS_START -->\n"

    for repo in repos:
        name = repo.get('name', 'Unknown')
        url = repo.get('url', '#')
        visibility = repo.get('visibility', 'PUBLIC').capitalize()
        stars = repo.get('stargazerCount', 0)

        lang = "N/A"
        if repo.get('primaryLanguage') and repo['primaryLanguage'].get('name'):
            lang = repo['primaryLanguage']['name']

        md_content += f"#### 🔹 [{name}]({url}) - `{visibility}` | ⭐️ {stars} | 🛠️ {lang}\n"

        # Commits
        commits_md = ""
        try:
            commits = repo['defaultBranchRef']['target']['history']['edges']
            if commits:
                commits_md += "<ul>"
                for edge in commits:
                    msg = edge['node']['messageHeadline']
                    commits_md += f"<li>{msg}</li>"
                commits_md += "</ul>"
            else:
                 commits_md += "<ul><li>_No recent commits_</li></ul>"
        except (KeyError, TypeError):
             commits_md += "<ul><li>_No commit data available_</li></ul>"

        md_content += commits_md + "\n"

    md_content += "<!-- DYNAMIC_REPOS_END -->"
    return md_content

def update_readme(new_content):
    readme_path = "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as file:
            readme_data = file.read()

        # Regex to replace everything between the tags
        pattern = re.compile(r"<!-- DYNAMIC_REPOS_START -->.*?<!-- DYNAMIC_REPOS_END -->", re.DOTALL)

        if not pattern.search(readme_data):
            print("Error: Could not find DYNAMIC_REPOS tags in README.md.")
            return False

        updated_data = pattern.sub(new_content, readme_data)

        with open(readme_path, "w", encoding="utf-8") as file:
            file.write(updated_data)
        return True
    except Exception as e:
        print(f"Error updating README.md: {e}")
        return False

if __name__ == "__main__":
    if TOKEN:
        print("GH_TOKEN found. Fetching real data via GraphQL...")
        repos = fetch_repos_graphql()
    else:
        print("No GH_TOKEN found. Using fallback mock data...")
        repos = get_mock_repos()

    if repos is not None:
        md_snippet = generate_markdown(repos)
        if update_readme(md_snippet):
             print("README.md updated successfully!")
        else:
             print("Failed to update README.md")
    else:
        print("Failed to get repository data.")
