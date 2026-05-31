import os
import re
import requests
from datetime import datetime

GITHUB_TOKEN = os.environ.get("GH_TOKEN")
USERNAME = "LaTortu3"

GRAPHQL_QUERY = """
query {
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
      nodes {
        name
        isPrivate
        stargazerCount
        primaryLanguage {
          name
        }
        url
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
""" % USERNAME

def get_repos_data():
    if not GITHUB_TOKEN:
        print("GH_TOKEN not found, using mock data for local testing.")
        return [
            {
                "name": "mock-repo-1",
                "isPrivate": False,
                "stargazerCount": 42,
                "primaryLanguage": {"name": "Python"},
                "url": "https://github.com/LaTortu3/mock-repo-1",
                "commits": [
                    {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T10:00:00Z"},
                    {"messageHeadline": "Add feature X", "committedDate": "2023-10-26T15:30:00Z"}
                ]
            },
            {
                "name": "mock-repo-private",
                "isPrivate": True,
                "stargazerCount": 0,
                "primaryLanguage": {"name": "C++"},
                "url": "https://github.com/LaTortu3/mock-repo-private",
                "commits": [
                    {"messageHeadline": "Fix memory leak", "committedDate": "2023-10-25T09:15:00Z"}
                ]
            }
        ]

    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": GRAPHQL_QUERY},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            print("GraphQL Errors:", data["errors"])
            return []

        nodes = data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])

        repos = []
        for node in nodes:
            commits = []
            try:
                commit_nodes = node["defaultBranchRef"]["target"]["history"]["nodes"]
                for c in commit_nodes:
                    commits.append({
                        "messageHeadline": c["messageHeadline"],
                        "committedDate": c["committedDate"]
                    })
            except (KeyError, TypeError):
                pass

            repos.append({
                "name": node["name"],
                "isPrivate": node["isPrivate"],
                "stargazerCount": node["stargazerCount"],
                "primaryLanguage": node["primaryLanguage"],
                "url": node["url"],
                "commits": commits
            })

        return repos

    except Exception as e:
        print(f"Error fetching data: {e}")
        return []

def format_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str

def generate_markdown(repos):
    if not repos:
        return "<p><i>Aucun dépôt trouvé ou erreur de chargement.</i></p>\n"

    md = ""
    for repo in repos:
        visibility_badge = "🔒 Private" if repo["isPrivate"] else "🌍 Public"
        stars = f"⭐ {repo['stargazerCount']}"
        lang = repo["primaryLanguage"]["name"] if repo["primaryLanguage"] else "N/A"

        md += f"#### [{repo['name']}]({repo['url']})\n"
        md += f"> {visibility_badge} | {stars} | 💻 {lang}\n\n"

        if repo["commits"]:
            md += "**Derniers commits :**\n"
            for c in repo["commits"]:
                date_formatted = format_date(c["committedDate"])
                md += f"- `{date_formatted}` : {c['messageHeadline']}\n"
        else:
            md += "*(Aucun commit récent)*\n"

        md += "\n---\n"

    return md

def update_readme(markdown_content):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # The markers
    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    pattern = re.compile(rf"({start_marker}).*?({end_marker})", re.DOTALL)

    if not pattern.search(content):
        print("Markers not found in README.md")
        return

    new_content = pattern.sub(rf"\1\n{markdown_content}\n\2", content)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md updated successfully.")

if __name__ == "__main__":
    repos = get_repos_data()
    md_content = generate_markdown(repos)
    update_readme(md_content)
