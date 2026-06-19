import os
import requests
import re

def get_repos():
    token = os.environ.get("GH_TOKEN")
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise ValueError("GH_TOKEN environment variable is missing in GitHub Actions environment.")
        print("Warning: GH_TOKEN missing, falling back to mock data.")
        return [
            {
                "name": "mock-repo-1",
                "url": "https://github.com/LaTortu3/mock-repo-1",
                "visibility": "PUBLIC",
                "stargazerCount": 42,
                "primaryLanguage": {"name": "Python"},
                "commits": [
                    "feat: initial mock commit",
                    "fix: resolve mock bug",
                    "docs: update mock readme"
                ]
            },
            {
                "name": "mock-private-repo",
                "url": "https://github.com/LaTortu3/mock-private-repo",
                "visibility": "PRIVATE",
                "stargazerCount": 10,
                "primaryLanguage": {"name": "JavaScript"},
                "commits": [
                    "chore: setup project",
                    "feat: add react components"
                ]
            }
        ]

    headers = {
        "Authorization": f"bearer {token}",
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
        raise Exception(f"GraphQL errors: {data['errors']}")

    repos_data = data["data"]["viewer"]["repositories"]["nodes"]
    parsed_repos = []

    for repo in repos_data:
        commits = []
        if repo.get("defaultBranchRef") and repo["defaultBranchRef"].get("target"):
            commits = [node["messageHeadline"] for node in repo["defaultBranchRef"]["target"]["history"]["nodes"]]

        parsed_repos.append({
            "name": repo["name"],
            "url": repo["url"],
            "visibility": repo["visibility"],
            "stargazerCount": repo["stargazerCount"],
            "primaryLanguage": repo.get("primaryLanguage") or {"name": "N/A"},
            "commits": commits
        })

    return parsed_repos

def format_repos_to_markdown(repos):
    md = ""
    for repo in repos:
        stars = f"⭐ {repo['stargazerCount']}" if repo['stargazerCount'] > 0 else ""
        lang = repo['primaryLanguage']['name'] if isinstance(repo.get('primaryLanguage'), dict) else "N/A"
        visibility = "🔒" if repo["visibility"] == "PRIVATE" else "🌍"

        md += f"#### [{visibility} {repo['name']}]({repo['url']}) {stars}\n"
        md += f"- **Langage principal :** {lang}\n"
        md += "- **Derniers commits :**\n"

        if not repo["commits"]:
            md += "  - Aucun commit récent.\n"
        else:
            for commit in repo["commits"]:
                md += f"  - `{commit}`\n"
        md += "\n"
    return md

def update_readme(md_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    pattern = re.compile(
        r"(<!-- DYNAMIC_REPOS_START -->\n)(.*?)(<!-- DYNAMIC_REPOS_END -->)",
        re.DOTALL
    )

    new_readme = pattern.sub(
        lambda m: f"{m.group(1)}{md_content}{m.group(3)}",
        readme_content
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    repos = get_repos()
    md_output = format_repos_to_markdown(repos)
    update_readme(md_output)
    print("README updated successfully!")
