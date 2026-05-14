import os
import re
import requests

GITHUB_TOKEN = os.getenv("GH_TOKEN")
USERNAME = "LaTortu3"

def fetch_repositories():
    if not GITHUB_TOKEN:
        print("GH_TOKEN not set. Make sure to set the environment variable.")
        return []

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    query = """
    {
      user(login: "LaTortu3") {
        repositories(first: 100, ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER], orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            description
            stargazerCount
            url
            isPrivate
            primaryLanguage {
              name
            }
            repositoryTopics(first: 5) {
              nodes {
                topic {
                  name
                }
              }
            }
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 3) {
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
    """

    response = requests.post('https://api.github.com/graphql', json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['user']['repositories']['nodes']
    else:
        print(f"Query failed to run by returning code of {response.status_code}. {response.text}")
        return []

def format_repo(repo):
    name = repo['name']
    url = repo['url']
    description = repo['description'] or "No description provided."
    stars = repo['stargazerCount']
    is_private = repo['isPrivate']

    visibility = "🔒 Private" if is_private else "🌐 Public"

    primary_language = repo.get('primaryLanguage')
    language_str = primary_language['name'] if primary_language else "Unknown"

    topics = [node['topic']['name'] for node in repo['repositoryTopics']['nodes']]
    topics_str = ", ".join(topics) if topics else "No topics"

    md = f"#### [{name}]({url}) - {visibility}\n"
    md += f"⭐ Stars: {stars} | 💻 Language: {language_str}\n"
    md += f"**Description:** {description}\n"
    if topics_str != "No topics":
         md += f"**Skills & Tech:** {topics_str}\n"

    md += "**Recent Commits:**\n"
    default_branch = repo.get('defaultBranchRef')
    if default_branch and default_branch.get('target'):
        commits = default_branch['target']['history']['nodes']
        if commits:
             for commit in commits:
                 date = commit.get('pushedDate', 'Unknown Date')
                 if date and 'T' in date:
                     date = date.split('T')[0]
                 msg = commit.get('messageHeadline', 'No message')
                 md += f"- `{date}`: {msg}\n"
        else:
             md += "- No recent commits found.\n"
    else:
        md += "- No recent commits found.\n"

    md += "\n"
    return md

def update_readme(new_content):
    with open('README.md', 'r', encoding='utf-8') as file:
        readme_contents = file.read()

    marker_start = "<!-- DYNAMIC_REPOS_START -->"
    marker_end = "<!-- DYNAMIC_REPOS_END -->"

    pattern = f"{marker_start}.*?{marker_end}"
    replacement = f"{marker_start}\n{new_content}\n{marker_end}"

    new_readme_contents = re.sub(pattern, replacement, readme_contents, flags=re.DOTALL)

    with open('README.md', 'w', encoding='utf-8') as file:
        file.write(new_readme_contents)

if __name__ == "__main__":
    repos = fetch_repositories()
    if repos:
        markdown_content = ""
        for repo in repos:
            markdown_content += format_repo(repo)

        update_readme(markdown_content)
        print("README.md updated successfully!")
    else:
        print("No repositories found or failed to fetch.")
