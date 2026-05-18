import os
import requests
import re

# Configuration
GITHUB_TOKEN = os.getenv('GH_TOKEN')
USERNAME = 'LaTortu3'
README_PATH = 'README.md'

if not GITHUB_TOKEN:
    print("Error: GH_TOKEN environment variable not set.")
    exit(1)

HEADERS = {
    'Authorization': f'bearer {GITHUB_TOKEN}',
    'Content-Type': 'application/json',
}

# GraphQL Query to fetch repos and their details
# Using pagination (first 100) to get a good chunk of repos
GRAPHQL_QUERY = """
{
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        url
        description
        isPrivate
        stargazerCount
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 3) {
                totalCount
                nodes {
                  messageHeadline
                  pushedDate
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

def fetch_repos():
    response = requests.post('https://api.github.com/graphql', json={'query': GRAPHQL_QUERY}, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        print(response.text)
        exit(1)

def generate_markdown(repos_data):
    try:
        repos = repos_data['data']['user']['repositories']['nodes']
    except KeyError as e:
        print(f"Unexpected JSON structure: {e}")
        print(repos_data)
        exit(1)

    markdown = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        description = repo['description'] or "Aucune description fournie."
        visibility_badge = "🔒 Privé" if repo['isPrivate'] else "🌍 Public"
        stars = repo['stargazerCount']

        # Get commit info
        total_commits = 0
        recent_commits = []
        try:
            history = repo['defaultBranchRef']['target']['history']
            total_commits = history['totalCount']
            recent_commits = history['nodes']
        except (KeyError, TypeError):
            # Might happen if repo has no commits or default branch is weird
            pass

        # Build repo entry
        markdown += f"#### [{name}]({url}) {visibility_badge} - ⭐️ {stars} étoiles\n"
        markdown += f"> {description}\n\n"

        markdown += f"- **Total Commits:** {total_commits}\n"
        if recent_commits:
            markdown += "- **Derniers Commits:**\n"
            for commit in recent_commits:
                msg = commit.get('messageHeadline', 'No message')
                markdown += f"  - 📝 {msg}\n"

        markdown += "\n---\n\n"

    return markdown

def update_readme(markdown_content):
    with open(README_PATH, 'r', encoding='utf-8') as f:
        readme_content = f.read()

    # The markers
    marker_start = '<!-- DYNAMIC_REPOS_START -->'
    marker_end = '<!-- DYNAMIC_REPOS_END -->'

    # Regex pattern to match everything between the markers
    pattern = f"({marker_start}).*?({marker_end})"

    # Replacement string with the new content
    replacement = f"\\1\n{markdown_content}\\2"

    # Check if markers exist
    if marker_start in readme_content and marker_end in readme_content:
        new_readme_content = re.sub(pattern, replacement, readme_content, flags=re.DOTALL)

        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_readme_content)
        print("README.md has been successfully updated!")
    else:
        print("Error: Could not find the dynamic markers in README.md.")
        exit(1)

if __name__ == "__main__":
    print("Fetching repositories...")
    data = fetch_repos()
    print("Generating markdown...")
    new_md = generate_markdown(data)
    print("Updating README.md...")
    update_readme(new_md)
    print("Done!")
