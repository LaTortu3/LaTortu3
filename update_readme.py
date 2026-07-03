import os
import re
import requests

def get_repos():
    token = os.environ.get("GH_TOKEN")
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise ValueError("GH_TOKEN environment variable is missing in GitHub Actions environment.")
        else:
            print("GH_TOKEN not found, using mock data for local testing.")
            return [
                {
                    "name": "mock-repo-1",
                    "url": "https://github.com/LaTortu3/mock-repo-1",
                    "visibility": "PUBLIC",
                    "stargazerCount": 5,
                    "primaryLanguage": {"name": "Python"},
                    "commits": [
                        {"message": "Initial commit", "committedDate": "2023-01-01T12:00:00Z"},
                        {"message": "Add feature X", "committedDate": "2023-01-02T12:00:00Z"}
                    ]
                },
                {
                    "name": "mock-repo-2",
                    "url": "https://github.com/LaTortu3/mock-repo-2",
                    "visibility": "PRIVATE",
                    "stargazerCount": 0,
                    "primaryLanguage": {"name": "JavaScript"},
                    "commits": [
                        {"message": "Fix bug Y", "committedDate": "2023-02-01T12:00:00Z"}
                    ]
                }
            ]

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

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

    response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)
    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        raise ValueError(f"GraphQL errors: {data['errors']}")

    repos = []
    for node in data["data"]["viewer"]["repositories"]["nodes"]:
        repo_data = {
            "name": node["name"],
            "url": node["url"],
            "visibility": node["visibility"],
            "stargazerCount": node["stargazerCount"],
            "primaryLanguage": node["primaryLanguage"],
            "commits": []
        }
        if node.get("defaultBranchRef") and node["defaultBranchRef"].get("target") and node["defaultBranchRef"]["target"].get("history"):
            for commit in node["defaultBranchRef"]["target"]["history"]["nodes"]:
                repo_data["commits"].append({
                    "message": commit["messageHeadline"],
                    "committedDate": commit["committedDate"]
                })
        repos.append(repo_data)

    return repos

def generate_markdown(repos):
    markdown = ""
    for i, repo in enumerate(repos, 1):
        lang = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else 'N/A'
        stars = repo['stargazerCount']
        visibility = "🔒 Privé" if repo["visibility"] == "PRIVATE" else "🌍 Public"

        markdown += f"{i}. **[{repo['name']}]({repo['url']})** ({visibility}) - ⭐ {stars} | 💻 {lang}\n"

        if repo['commits']:
            markdown += "   - *Derniers commits :*\n"
            for commit in repo['commits']:
                date = commit['committedDate'][:10]
                markdown += f"     - `{date}`: {commit['message']}\n"
        else:
            markdown += "   - *Aucun commit récent trouvé.*\n"
        markdown += "\n"
    return markdown

def update_readme(new_content):
    with open("README.md", "r") as f:
        readme = f.read()

    pattern = r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)'

    # Use lambda to avoid backreference issues if new_content has backslashes
    new_readme = re.sub(
        pattern,
        lambda m: f"{m.group(1)}{new_content}{m.group(2)}",
        readme,
        flags=re.DOTALL
    )

    with open("README.md", "w") as f:
        f.write(new_readme)

if __name__ == "__main__":
    print("Fetching repositories...")
    repos = get_repos()
    print(f"Found {len(repos)} repositories.")
    markdown = generate_markdown(repos)
    print("Updating README.md...")
    update_readme(markdown)
    print("Done!")
