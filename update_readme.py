import os
import requests
import re

def fetch_repos(token):
    # GraphQL query to get user's public and private repositories,
    # including stars, primary language, and the latest commit info.
    query = """
    {
      viewer {
        repositories(first: 100, affiliations: [OWNER], isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            description
            isPrivate
            stargazerCount
            url
            primaryLanguage {
              name
            }
            defaultBranchRef {
              target {
                ... on Commit {
                  messageHeadline
                  pushedDate
                }
              }
            }
          }
        }
      }
    }
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://api.github.com/graphql", json={"query": query}, headers=headers)
    response.raise_for_status()
    data = response.json()
    if 'errors' in data:
        raise Exception(f"GraphQL errors: {data['errors']}")
    return data['data']['viewer']['repositories']['nodes']

def generate_markdown(repos):
    markdown = ""
    for repo in repos:
        name = repo['name']
        description = repo['description'] or "No description provided."
        is_private = repo['isPrivate']
        stars = repo['stargazerCount']
        lang = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "N/A"

        commit_msg = "No recent commits"
        commit_date = ""
        if repo['defaultBranchRef'] and repo['defaultBranchRef']['target']:
            target = repo['defaultBranchRef']['target']
            if 'messageHeadline' in target:
                commit_msg = target['messageHeadline']
            if 'pushedDate' in target:
                # Format date string roughly
                commit_date = target['pushedDate'].split('T')[0]
                commit_msg += f" ({commit_date})"

        visibility = "🔒 Private" if is_private else "🌍 Public"
        url = repo.get('url', f'https://github.com/LaTortu3/{name}')

        markdown += f"#### [{name}]({url}) {visibility} | ⭐ {stars}\n"
        markdown += f"- **Tech/Language:** {lang}\n"
        markdown += f"- **Description:** {description}\n"
        markdown += f"- **Latest Update:** {commit_msg}\n\n"

    return markdown

def update_readme(markdown_content):
    with open("README.md", "r", encoding="utf-8") as file:
        readme_contents = file.read()

    # The markers in the README
    start_marker = "<!-- DYNAMIC_REPOS_START -->"
    end_marker = "<!-- DYNAMIC_REPOS_END -->"

    pattern = f"({start_marker}).*?({end_marker})"

    # Use a lambda to avoid backreference parsing issues with dynamic content
    new_contents = re.sub(
        pattern,
        lambda match: f"{match.group(1)}\n{markdown_content}{match.group(2)}",
        readme_contents,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as file:
        file.write(new_contents)

def main():
    token = os.environ.get("GH_TOKEN")
    if not token:
        print("GH_TOKEN environment variable not set. Please set it and try again.")
        return

    try:
        repos = fetch_repos(token)
        markdown_content = generate_markdown(repos)
        update_readme(markdown_content)
        print("Successfully updated README.md with dynamic repository data.")
    except Exception as e:
        print(f"Error fetching or parsing repos: {e}")

if __name__ == "__main__":
    main()
