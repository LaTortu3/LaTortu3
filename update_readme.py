import os
import requests
import re

def fetch_repos():
    token = os.environ.get("GH_TOKEN")
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_ci:
            raise ValueError("GH_TOKEN environment variable is required in GitHub Actions.")
        else:
            print("GH_TOKEN not found. Using mock data for local testing.")
            return [
                {
                    "name": "mock-repo-1",
                    "url": "https://github.com/LaTortu3/mock-repo-1",
                    "visibility": "PUBLIC",
                    "stargazerCount": 5,
                    "primaryLanguage": {"name": "Python"},
                    "defaultBranchRef": {
                        "target": {
                            "history": {
                                "nodes": [
                                    {"messageHeadline": "Initial commit", "committedDate": "2023-10-27T12:00:00Z"},
                                    {"messageHeadline": "Added feature X", "committedDate": "2023-10-27T14:00:00Z"}
                                ]
                            }
                        }
                    }
                },
                 {
                    "name": "mock-repo-2",
                    "url": "https://github.com/LaTortu3/mock-repo-2",
                    "visibility": "PRIVATE",
                    "stargazerCount": 10,
                    "primaryLanguage": {"name": "JavaScript"},
                    "defaultBranchRef": {
                        "target": {
                            "history": {
                                "nodes": [
                                    {"messageHeadline": "Fix bug Y", "committedDate": "2023-10-26T12:00:00Z"}
                                ]
                            }
                        }
                    }
                }
            ]

    query = """
    query {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, affiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
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

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

    data = response.json()
    if 'errors' in data:
         raise Exception(f"GraphQL errors: {data['errors']}")

    return data["data"]["viewer"]["repositories"]["nodes"]

def format_repos_md(repos):
    md = ""
    for repo in repos[:5]: # Take top 5 recent repos
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        visibility = repo.get("visibility", "PUBLIC")
        stars = repo.get("stargazerCount", 0)

        primary_lang = repo.get("primaryLanguage")
        lang_str = primary_lang.get("name", "Unknown") if primary_lang else "Unknown"

        visibility_badge = f"![{visibility}](https://img.shields.io/badge/{visibility}-gray?style=flat-square)"
        stars_badge = f"![Stars](https://img.shields.io/badge/⭐-{stars}-yellow?style=flat-square)"

        md += f"#### [{name}]({url}) {visibility_badge} {stars_badge}\n"
        md += f"- **Langage principal :** {lang_str}\n"

        branch_ref = repo.get("defaultBranchRef")
        if branch_ref:
             history = branch_ref.get("target", {}).get("history", {}).get("nodes", [])
             if history:
                 md += "- **Derniers commits :**\n"
                 for commit in history:
                     msg = commit.get("messageHeadline", "")
                     date = commit.get("committedDate", "")[:10]
                     md += f"  - `{date}` : {msg}\n"
             else:
                 md += "- *Aucun commit récent*\n"
        else:
            md += "- *Aucun historique de commits*\n"

        md += "\n"
    return md

def update_readme(new_content):
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()

        # Regex to find the start and end markers, replacing strictly between them.
        pattern = r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)"

        # Lambda function to prevent backreference parsing errors with re.sub
        replacement = lambda m: f"{m.group(1)}{new_content}{m.group(2)}"

        new_readme, num_subs = re.subn(pattern, replacement, content, flags=re.DOTALL)

        if num_subs == 0:
             print("Warning: Dynamic markers not found in README.md.")
             return False

        with open("README.md", "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("README.md updated successfully.")
        return True
    except FileNotFoundError:
        print("README.md not found.")
        return False

if __name__ == "__main__":
    print("Fetching repositories...")
    repos = fetch_repos()
    print(f"Fetched {len(repos)} repositories.")

    print("Formatting repository data...")
    repos_md = format_repos_md(repos)

    print("Updating README.md...")
    update_readme(repos_md)
