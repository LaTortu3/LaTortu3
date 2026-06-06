import os
import requests
import re

USERNAME = "LaTortu3"
TOKEN = os.getenv("GH_TOKEN")
README_PATH = "README.md"
START_MARKER = "<!-- DYNAMIC_REPOS_START -->"
END_MARKER = "<!-- DYNAMIC_REPOS_END -->"

GRAPHQL_QUERY = """
query {
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
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
                    oid
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
""" % USERNAME

def get_repos_data():
    if not TOKEN:
        print("No GH_TOKEN found. Using mock data.")
        return [
            {
                "name": "MockRepo-1",
                "url": "https://github.com/LaTortu3/MockRepo-1",
                "visibility": "PUBLIC",
                "stargazerCount": 5,
                "primaryLanguage": {"name": "Python"},
                "defaultBranchRef": {
                    "target": {
                        "history": {
                            "edges": [
                                {"node": {"messageHeadline": "Initial commit", "oid": "a1b2c3d4e5"}},
                                {"node": {"messageHeadline": "Update README.md", "oid": "f6g7h8i9j0"}},
                            ]
                        }
                    }
                }
            },
            {
                "name": "MockRepo-Private",
                "url": "https://github.com/LaTortu3/MockRepo-Private",
                "visibility": "PRIVATE",
                "stargazerCount": 0,
                "primaryLanguage": {"name": "C++"},
                "defaultBranchRef": None
            }
        ]

    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.post("https://api.github.com/graphql", json={"query": GRAPHQL_QUERY}, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if "errors" in data:
            print("GraphQL Errors:", data["errors"])
            return []
        return data["data"]["user"]["repositories"]["nodes"]
    else:
        print(f"Request failed with status code {response.status_code}")
        return []

def format_repo(repo):
    name = repo.get("name", "Unknown")
    url = repo.get("url", "#")
    visibility = repo.get("visibility", "PUBLIC")
    stars = repo.get("stargazerCount", 0)
    lang_node = repo.get("primaryLanguage")
    language = lang_node.get("name") if lang_node else "N/A"

    markdown = f"### 📁 [{name}]({url}) ({visibility.capitalize()})\n"
    markdown += f"⭐ **Stars:** {stars} | 📝 **Language:** {language}\n\n"

    branch_ref = repo.get("defaultBranchRef")
    if branch_ref and branch_ref.get("target") and branch_ref["target"].get("history") and branch_ref["target"]["history"].get("edges"):
        commits = branch_ref["target"]["history"]["edges"]
        markdown += "**Latest Commits:**\n"
        for edge in commits:
            commit = edge["node"]
            msg = commit.get("messageHeadline", "")
            oid = commit.get("oid", "")[:7]
            markdown += f"- `{oid}` - {msg}\n"
    else:
        markdown += "*No recent commits found.*\n"

    return markdown

def update_readme(new_content):
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(rf"{START_MARKER}.*?{END_MARKER}", re.DOTALL)
    replacement = f"{START_MARKER}\n\n{new_content}\n\n{END_MARKER}"

    if re.search(pattern, content):
        updated_content = re.sub(pattern, lambda m: replacement, content)
    else:
        print("Markers not found in README.md. Please add them.")
        return False

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated_content)
    return True

if __name__ == "__main__":
    repos = get_repos_data()
    repos_md = []
    for repo in repos:
        repos_md.append(format_repo(repo))

    final_md = "\n".join(repos_md)
    if update_readme(final_md):
        print("README.md updated successfully.")
    else:
        print("Failed to update README.md.")
