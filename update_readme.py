import os
import requests
import json
import re

GITHUB_TOKEN = os.getenv("GH_TOKEN")
IS_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS") == "true"

def fetch_repos():
    if not GITHUB_TOKEN:
        if IS_GITHUB_ACTIONS:
            raise ValueError("GH_TOKEN is missing in a GitHub Actions environment. Aborting to avoid mock data injection.")
        print("GH_TOKEN is missing. Using mock data for local testing.")
        return get_mock_data()

    url = 'https://api.github.com/graphql'
    headers = {
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Content-Type': 'application/json',
    }

    query = """
    query {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: [OWNER]) {
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

    response = requests.post(url, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['viewer']['repositories']['nodes']
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def get_mock_data():
    return [
        {
            "name": "mock-repo-1",
            "url": "https://github.com/LaTortu3/mock-repo-1",
            "visibility": "PUBLIC",
            "stargazerCount": 42,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Initial commit", "committedDate": "2023-10-01T12:00:00Z"},
                            {"messageHeadline": "Add feature X", "committedDate": "2023-10-02T12:00:00Z"},
                            {"messageHeadline": "Fix bug Y", "committedDate": "2023-10-03T12:00:00Z"}
                        ]
                    }
                }
            }
        },
        {
            "name": "mock-repo-private",
            "url": "https://github.com/LaTortu3/mock-repo-private",
            "visibility": "PRIVATE",
            "stargazerCount": 5,
            "primaryLanguage": {"name": "JavaScript"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": [
                            {"messageHeadline": "Initial private commit", "committedDate": "2023-09-01T12:00:00Z"}
                        ]
                    }
                }
            }
        }
    ]

def generate_markdown(repos):
    markdown = ""
    for repo in repos:
        name = repo.get("name", "Unknown")
        url = repo.get("url", "#")
        visibility = repo.get("visibility", "PUBLIC")
        stars = repo.get("stargazerCount", 0)

        lang = repo.get("primaryLanguage")
        language = lang.get("name", "N/A") if lang else "N/A"

        vis_badge = "🔒 Private" if visibility == "PRIVATE" else "🌍 Public"

        markdown += f"#### [{name}]({url}) - {vis_badge}\n"
        markdown += f"- **Language:** {language} | **Stars:** ⭐ {stars}\n"
        markdown += "- **Recent Commits:**\n"

        try:
            commits = repo["defaultBranchRef"]["target"]["history"]["nodes"]
            if not commits:
                markdown += "  - No recent commits.\n"
            else:
                for commit in commits:
                    date = commit.get("committedDate", "")[:10]
                    msg = commit.get("messageHeadline", "")
                    markdown += f"  - `[{date}]` {msg}\n"
        except (TypeError, KeyError):
            markdown += "  - No commit data available.\n"

        markdown += "\n"
    return markdown

def update_readme(markdown_content):
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()

    marker_start = "<!-- DYNAMIC_REPOS_START -->"
    marker_end = "<!-- DYNAMIC_REPOS_END -->"

    pattern = re.compile(rf"{marker_start}.*?{marker_end}", re.DOTALL)

    new_section = f"{marker_start}\n{markdown_content}{marker_end}"

    new_content = re.sub(pattern, new_section, content)

    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(new_content)

    print("README.md updated successfully.")

if __name__ == "__main__":
    try:
        repos = fetch_repos()
        md_output = generate_markdown(repos)
        update_readme(md_output)
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
