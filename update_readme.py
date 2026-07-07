import os
import re
import requests

def get_repositories(token):
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
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
    response = requests.post(url, json={"query": query}, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {query}")

    data = response.json()
    if 'errors' in data:
        raise Exception(f"GraphQL errors: {data['errors']}")

    return data['data']['viewer']['repositories']['nodes']

def generate_markdown(repositories):
    markdown = ""
    for repo in repositories:
        lang = repo.get('primaryLanguage')
        lang_str = lang['name'] if lang else 'N/A'

        markdown += f"#### 📁 [{repo['name']}]({repo['url']})\n"
        markdown += f"**Visibility:** {repo['visibility']} | **⭐ Stars:** {repo['stargazerCount']} | **Language:** {lang_str}\n\n"

        default_branch = repo.get('defaultBranchRef')
        if default_branch and default_branch.get('target') and default_branch['target'].get('history'):
            commits = default_branch['target']['history']['nodes']
            if commits:
                markdown += "**Derniers Commits:**\n"
                for commit in commits:
                    date_str = commit['committedDate'][:10]
                    markdown += f"- `{date_str}`: {commit['messageHeadline']}\n"
        markdown += "\n"
    return markdown

def get_mock_markdown():
    return """#### 📁 [mock-repo](https://github.com/mock/mock-repo)
**Visibility:** PUBLIC | **⭐ Stars:** 42 | **Language:** Python

**Derniers Commits:**
- `2023-10-27`: Initial commit
- `2023-10-27`: Update README
- `2023-10-28`: Add new feature

"""

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure lambda is used for replacement to prevent backreference errors
    pattern = r'(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)'
    new_readme = re.sub(pattern, lambda m: f'{m.group(1)}{new_content}{m.group(2)}', content, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    token = os.environ.get("GH_TOKEN")
    is_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    if not token:
        if is_github_actions:
            raise Exception("GH_TOKEN is missing. Cannot fetch repositories in GitHub Actions environment.")
        else:
            print("GH_TOKEN not found. Using mock data for local testing.")
            new_content = get_mock_markdown()
    else:
        print("Fetching repositories from GitHub GraphQL API...")
        repos = get_repositories(token)
        new_content = generate_markdown(repos)

    update_readme(new_content)
    print("README.md updated successfully.")
