import os
import requests
import re

GITHUB_TOKEN = os.getenv("GH_TOKEN")
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

def fetch_repos():
    # Fallback for local testing
    if not GITHUB_TOKEN:
        if IS_GITHUB_ACTIONS:
            raise ValueError("GH_TOKEN is missing in GitHub Actions environment.")
        print("GH_TOKEN missing, returning mock data for local testing.")
        return [
            {
                "name": "mock-repo-1",
                "url": "https://github.com/LaTortu3/mock-repo-1",
                "isPrivate": False,
                "stargazerCount": 5,
                "primaryLanguage": {"name": "Python"},
                "commits": [
                    {"message": "Initial commit"},
                    {"message": "Add feature X"},
                    {"message": "Fix bug Y"}
                ]
            },
            {
                "name": "mock-private-repo-2",
                "url": "https://github.com/LaTortu3/mock-private-repo-2",
                "isPrivate": True,
                "stargazerCount": 2,
                "primaryLanguage": {"name": "JavaScript"},
                "commits": [
                    {"message": "Update deps"},
                    {"message": "Refactor UI"}
                ]
            }
        ]

    # GraphQL query
    query = """
    query {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
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
    """

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data: {response.status_code} - {response.text}")

    result = response.json()
    if "errors" in result:
        raise Exception(f"GraphQL errors: {result['errors']}")

    repos = []
    for node in result["data"]["viewer"]["repositories"]["nodes"]:
        commits = []
        if node.get("defaultBranchRef") and node["defaultBranchRef"].get("target") and node["defaultBranchRef"]["target"].get("history"):
            commits = [{"message": c["messageHeadline"]} for c in node["defaultBranchRef"]["target"]["history"]["nodes"]]

        repos.append({
            "name": node["name"],
            "url": node["url"],
            "isPrivate": node["isPrivate"],
            "stargazerCount": node["stargazerCount"],
            "primaryLanguage": node.get("primaryLanguage") or {"name": "N/A"},
            "commits": commits
        })

    return repos

def format_repo(repo):
    privacy_badge = "🔒 Private" if repo["isPrivate"] else "🌐 Public"
    stars = f"⭐ {repo['stargazerCount']}"
    lang = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "N/A"

    content = f"#### [{repo['name']}]({repo['url']})\n"
    content += f"_{privacy_badge} | {stars} | {lang}_\n\n"
    if repo["commits"]:
        content += "**Derniers commits:**\n"
        for commit in repo["commits"]:
            content += f"- `{commit['message']}`\n"
    else:
        content += "- _Aucun commit récent_\n"

    return content

def update_readme(repos):
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            readme_content = f.read()
    except FileNotFoundError:
        print("README.md not found.")
        return

    repo_text = ""
    for repo in repos:
        repo_text += format_repo(repo) + "\n"

    # Use re.sub with lambda to avoid backreference parsing errors with replacement string
    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

    def repl(m):
        return f"{m.group(1)}{repo_text}{m.group(2)}"

    updated_content = re.sub(pattern, repl, readme_content, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_content)

    print("README.md updated successfully!")

if __name__ == "__main__":
    repos = fetch_repos()
    update_readme(repos)
