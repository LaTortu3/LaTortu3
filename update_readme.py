import os
import re
import requests

GITHUB_USERNAME = "LaTortu3"
GH_TOKEN = os.getenv("GH_TOKEN")
README_PATH = "README.md"
START_MARKER = "<!-- DYNAMIC_REPOS_START -->"
END_MARKER = "<!-- DYNAMIC_REPOS_END -->"

GRAPHQL_QUERY = """
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

MOCK_DATA = [
    {
        "name": "mock-repo-1",
        "stargazerCount": 42,
        "primaryLanguage": {"name": "Python"},
        "defaultBranchRef": {
            "target": {
                "history": {
                    "edges": [
                        {"node": {"messageHeadline": "Initial commit", "committedDate": "2024-05-01T10:00:00Z"}},
                        {"node": {"messageHeadline": "Update README", "committedDate": "2024-05-02T12:00:00Z"}},
                        {"node": {"messageHeadline": "Fix typo", "committedDate": "2024-05-03T14:30:00Z"}},
                    ]
                }
            }
        }
    },
    {
        "name": "mock-repo-2",
        "stargazerCount": 10,
        "primaryLanguage": {"name": "JavaScript"},
        "defaultBranchRef": {
            "target": {
                "history": {
                    "edges": [
                        {"node": {"messageHeadline": "Add new feature", "committedDate": "2024-05-04T09:15:00Z"}},
                    ]
                }
            }
        }
    }
]

def fetch_repositories():
    if not GH_TOKEN:
        print("Warning: GH_TOKEN not set. Using mock data.")
        return MOCK_DATA

    headers = {"Authorization": f"Bearer {GH_TOKEN}"}
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": GRAPHQL_QUERY},
            headers=headers
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            print(f"GraphQL Error: {data['errors']}")
            return MOCK_DATA
        return data["data"]["user"]["repositories"]["nodes"]
    except Exception as e:
        print(f"Error fetching data: {e}. Using mock data.")
        return MOCK_DATA

def format_repositories(repos):
    markdown = "\n"
    for repo in repos:
        name = repo.get("name", "Unknown")
        stars = repo.get("stargazerCount", 0)

        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name") if lang_node else "N/A"

        markdown += f"#### 📦 [{name}](https://github.com/{GITHUB_USERNAME}/{name}) ⭐ {stars} | 🛠️ {lang}\n"
        markdown += "Derniers commits :\n"

        branch_ref = repo.get("defaultBranchRef")
        if branch_ref and branch_ref.get("target") and branch_ref["target"].get("history"):
            commits = branch_ref["target"]["history"]["edges"]
            for commit_edge in commits:
                commit = commit_edge.get("node", {})
                message = commit.get("messageHeadline", "")
                date = commit.get("committedDate", "")[:10]  # Just the date part
                markdown += f"- `{date}` : {message}\n"
        else:
            markdown += "- Aucun commit récent trouvé.\n"
        markdown += "\n"
    return markdown

def update_readme(markdown_content):
    with open(README_PATH, "r", encoding="utf-8") as f:
        readme_content = f.read()

    pattern = re.compile(rf"({START_MARKER}).*?({END_MARKER})", re.DOTALL)

    if not pattern.search(readme_content):
        print(f"Markers {START_MARKER} and {END_MARKER} not found in README.md")
        return False

    new_content = pattern.sub(rf"\1\n{markdown_content}\2", readme_content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    return True

if __name__ == "__main__":
    repos = fetch_repositories()
    markdown = format_repositories(repos)
    if update_readme(markdown):
        print("README.md updated successfully!")
    else:
        print("Failed to update README.md")
