import os
import requests

GITHUB_TOKEN = os.getenv("GH_TOKEN")
USERNAME = "LaTortu3"

def fetch_repositories():
    if not GITHUB_TOKEN:
        print("GH_TOKEN not found. Returning mock data.")
        return get_mock_data()

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }

    query = """
    query {
      user(login: "%s") {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: [OWNER, COLLABORATOR]) {
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
    """ % USERNAME

    try:
        response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)
        response.raise_for_status()
        data = response.json()
        if 'errors' in data:
            print("GraphQL Errors:", data['errors'])
            return get_mock_data()
        return data.get("data", {}).get("user", {}).get("repositories", {}).get("nodes", [])
    except Exception as e:
        print(f"Failed to fetch repositories: {e}")
        return get_mock_data()

def get_mock_data():
    return [
        {
            "name": "MockRepo1",
            "stargazerCount": 42,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Initial commit"},
                            {"messageHeadline": "Added new feature"},
                            {"messageHeadline": "Fixed a bug"}
                        ]
                    }
                }
            }
        },
        {
            "name": "MockRepo2",
            "stargazerCount": 15,
            "primaryLanguage": {"name": "JavaScript"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Updated README"},
                            {"messageHeadline": "Refactored code"}
                        ]
                    }
                }
            }
        }
    ]

def format_repo_data(repos):
    output = []
    for repo in repos:
        name = repo.get("name", "Unknown Repo")
        stars = repo.get("stargazerCount", 0)
        lang_node = repo.get("primaryLanguage")
        lang = lang_node.get("name") if lang_node else "N/A"

        output.append(f"#### 🌟 {name} ({stars} ⭐) - {lang}")

        branch_ref = repo.get("defaultBranchRef")
        if branch_ref and branch_ref.get("target") and branch_ref["target"].get("history") and branch_ref["target"]["history"].get("nodes"):
            commits = branch_ref["target"]["history"]["nodes"]
            output.append("  *Commits récents:*")
            for commit in commits:
                msg = commit.get("messageHeadline", "").strip()
                if msg:
                    output.append(f"  - `{msg}`")
        else:
            output.append("  *Aucun commit récent.*")
        output.append("") # Empty line for spacing
    return "\n".join(output)

def update_readme(content):
    readme_path = "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_text = f.read()

        start_marker = "<!-- DYNAMIC_REPOS_START -->"
        end_marker = "<!-- DYNAMIC_REPOS_END -->"

        start_index = readme_text.find(start_marker)
        end_index = readme_text.find(end_marker)

        if start_index == -1 or end_index == -1:
            print("Markers not found in README.md")
            return

        new_readme = readme_text[:start_index + len(start_marker)] + "\n" + content + "\n" + readme_text[end_index:]

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("README.md updated successfully.")
    except Exception as e:
        print(f"Failed to update README.md: {e}")

if __name__ == "__main__":
    repos = fetch_repositories()
    formatted_content = format_repo_data(repos)
    update_readme(formatted_content)
