import os
import requests
import re
from datetime import datetime

# Configuration
GITHUB_TOKEN = os.getenv("GH_TOKEN")
USERNAME = "LaTortu3"
README_PATH = "README.md"
START_MARKER = "<!-- DYNAMIC_REPOS_START -->"
END_MARKER = "<!-- DYNAMIC_REPOS_END -->"

GRAPHQL_URL = "https://api.github.com/graphql"

QUERY = """
query {
  user(login: "%s") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
      nodes {
        name
        url
        description
        isPrivate
        stargazerCount
        primaryLanguage {
          name
          color
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history(first: 3) {
                nodes {
                  messageHeadline
                  committedDate
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
""" % USERNAME

def get_mock_data():
    return [
        {
            "name": "mock-repo-1",
            "url": "https://github.com/LaTortu3/mock-repo-1",
            "description": "A mock repository for local testing.",
            "isPrivate": False,
            "stargazerCount": 42,
            "primaryLanguage": {"name": "Python", "color": "#3572A5"},
            "commits": [
                {"messageHeadline": "Update README", "date": "2023-10-27T10:00:00Z", "oid": "a1b2c3d"},
                {"messageHeadline": "Fix bug", "date": "2023-10-26T15:30:00Z", "oid": "e4f5g6h"},
                {"messageHeadline": "Initial commit", "date": "2023-10-25T09:00:00Z", "oid": "i7j8k9l"}
            ]
        },
        {
            "name": "secret-project",
            "url": "https://github.com/LaTortu3/secret-project",
            "description": "Top secret stuff.",
            "isPrivate": True,
            "stargazerCount": 0,
            "primaryLanguage": {"name": "C++", "color": "#f34b7d"},
            "commits": [
                {"messageHeadline": "Optimize render loop", "date": "2023-10-27T12:00:00Z", "oid": "z1x2c3v"}
            ]
        }
    ]

def fetch_repos():
    if not GITHUB_TOKEN:
        print("GH_TOKEN not found. Using mock data.")
        return get_mock_data()

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(GRAPHQL_URL, json={'query': QUERY}, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch data: {response.status_code} - {response.text}")
        return get_mock_data()

    data = response.json()
    if "errors" in data:
        print(f"GraphQL errors: {data['errors']}")
        return get_mock_data()

    repos = []
    try:
        nodes = data['data']['user']['repositories']['nodes']
        for node in nodes:
            commits = []
            if node.get('defaultBranchRef') and node['defaultBranchRef'].get('target') and node['defaultBranchRef']['target'].get('history'):
                for commit in node['defaultBranchRef']['target']['history']['nodes']:
                    commits.append({
                        "messageHeadline": commit['messageHeadline'],
                        "date": commit['committedDate'],
                        "oid": commit['oid'][:7]
                    })

            repos.append({
                "name": node['name'],
                "url": node['url'],
                "description": node.get('description') or "",
                "isPrivate": node['isPrivate'],
                "stargazerCount": node['stargazerCount'],
                "primaryLanguage": node.get('primaryLanguage'),
                "commits": commits
            })
    except KeyError as e:
        print(f"Error parsing response: {e}")
        return get_mock_data()

    return repos

def generate_markdown(repos):
    if not repos:
        return "No repositories found.\n"

    md = "### 📂 Mes Dépôts Récents & Avancées\n\n"

    for repo in repos:
        # Repository Name and Link
        private_badge = " 🔒 `Privé`" if repo['isPrivate'] else " 🌐 `Public`"
        md += f"#### [{repo['name']}]({repo['url']}){private_badge}\n"

        # Description
        if repo['description']:
            md += f"> {repo['description']}\n\n"

        # Stats (Stars, Language)
        stats = []
        if repo['stargazerCount'] > 0:
            stats.append(f"⭐ {repo['stargazerCount']}")
        if repo['primaryLanguage']:
            stats.append(f"🟢 **{repo['primaryLanguage']['name']}**")

        if stats:
            md += " | ".join(stats) + "\n\n"

        # Commits
        if repo['commits']:
            md += "**Derniers Commits :**\n"
            for commit in repo['commits']:
                date_str = datetime.strptime(commit['date'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d %b %Y")
                md += f"- `{commit['oid']}` ({date_str}) : {commit['messageHeadline']}\n"
        else:
            md += "_Aucun commit récent._\n"

        md += "\n---\n\n"

    return md

def update_readme(markdown_content):
    if not os.path.exists(README_PATH):
        print(f"{README_PATH} not found.")
        return

    with open(README_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace content between markers
    pattern = re.compile(rf"({START_MARKER}).*?({END_MARKER})", re.DOTALL)

    if pattern.search(content):
        new_content = pattern.sub(lambda m: f"{m.group(1)}\n{markdown_content}\n{m.group(2)}", content)
        with open(README_PATH, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("README.md updated successfully.")
    else:
        print(f"Markers {START_MARKER} and {END_MARKER} not found in README.md")

if __name__ == "__main__":
    repos = fetch_repos()
    md_content = generate_markdown(repos)
    update_readme(md_content)
