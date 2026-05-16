import os
import requests
import re

GITHUB_TOKEN = os.getenv("GH_TOKEN")
USERNAME = "LaTortu3"

if not GITHUB_TOKEN:
    print("Warning: GH_TOKEN not found in environment. The script might not be able to fetch private repositories.")

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}" if GITHUB_TOKEN else "",
    "Content-Type": "application/json",
}

# We use the GraphQL API to get public and private repos (using viewer instead of user)
# Since we might not be authenticated as LaTortu3 in local testing without the proper token,
# we will fallback to fetching for LaTortu3 as a user if viewer doesn't match or token is missing,
# but the action should run with a token that gives access to viewer's private repos.
GRAPHQL_QUERY = """
query {
  user(login: "LaTortu3") {
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name
        url
        description
        stargazerCount
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

# Viewer query gets private repos if the token belongs to LaTortu3
VIEWER_QUERY = """
query {
  viewer {
    login
    repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}, ownerAffiliations: OWNER) {
      nodes {
        name
        url
        description
        stargazerCount
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

def fetch_repos():
    # Try viewer query first to get private repos
    if GITHUB_TOKEN:
        response = requests.post(
            "https://api.github.com/graphql",
            json={"query": VIEWER_QUERY},
            headers=HEADERS
        )
        if response.status_code == 200:
            data = response.json()
            if "data" in data and data["data"].get("viewer"):
                if data["data"]["viewer"]["login"].lower() == USERNAME.lower():
                    return data["data"]["viewer"]["repositories"]["nodes"]
                else:
                     print(f"Token belongs to {data['data']['viewer']['login']}, falling back to user query for {USERNAME}.")
        else:
             print(f"Viewer query failed: {response.text}")

    # Fallback to user query (only gets public repos for that user, or what the token is allowed to see)
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": GRAPHQL_QUERY},
        headers=HEADERS
    )
    if response.status_code == 200:
        data = response.json()
        if "data" in data and data["data"].get("user"):
             return data["data"]["user"]["repositories"]["nodes"]
        else:
            print("Could not find user data in response.")
            return []
    else:
        print(f"User query failed with status code {response.status_code}: {response.text}")
        return []

def format_repos(repos):
    markdown = ""
    for repo in repos:
        # Basic Info
        name = repo.get("name", "Unknown Repo")
        url = repo.get("url", "#")
        desc = repo.get("description") or "Pas de description"
        stars = repo.get("stargazerCount", 0)
        is_private = repo.get("isPrivate", False)

        visibility = "🔒 Privé" if is_private else "🌐 Public"
        star_str = f"⭐ {stars}" if stars > 0 else "⭐ 0"

        # Skills & Tech
        lang = repo.get("primaryLanguage")
        lang_name = lang.get("name") if lang else "Non défini"

        topics_data = repo.get("repositoryTopics", {}).get("nodes", [])
        topics = [t["topic"]["name"] for t in topics_data if t and "topic" in t]

        tech_stack = f"**Langage Principal:** {lang_name}"
        if topics:
             tech_stack += f" | **Technologies & Skills:** {', '.join(topics)}"

        # Commits
        commits_md = ""
        default_branch = repo.get("defaultBranchRef")
        if default_branch and default_branch.get("target") and default_branch["target"].get("history"):
            commits = default_branch["target"]["history"].get("nodes", [])
            if commits:
                commits_md = "\n**Derniers Commits :**\n"
                for commit in commits:
                    msg = commit.get("messageHeadline", "").strip()
                    date = commit.get("pushedDate", "")
                    # Simple date formatting: 2023-10-25T... -> 2023-10-25
                    if date and len(date) >= 10:
                        date = date[:10]
                    commits_md += f"- `{date}` : {msg}\n"

        # Build Markdown Block
        markdown += f"#### [{name}]({url}) ({visibility}) {star_str}\n"
        markdown += f"> {desc}\n>\n"
        markdown += f"> {tech_stack}\n"
        if commits_md:
             markdown += f"{commits_md}\n"
        markdown += "---\n\n"

    return markdown

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    # Use regex to find and replace the content between markers
    marker_start = "<!-- DYNAMIC_REPOS_START -->"
    marker_end = "<!-- DYNAMIC_REPOS_END -->"

    pattern = f"({marker_start}).*?({marker_end})"

    # Check if markers exist
    if marker_start not in readme or marker_end not in readme:
        print("Markers not found in README.md. Please make sure <!-- DYNAMIC_REPOS_START --> and <!-- DYNAMIC_REPOS_END --> exist.")
        return

    # Replace using regex, dotall enables matching across newlines
    updated_readme = re.sub(pattern, lambda m: f"{m.group(1)}\n{new_content}\n{m.group(2)}", readme, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_readme)

    print("README.md successfully updated!")

if __name__ == "__main__":
    repos = fetch_repos()
    if repos:
        print(f"Found {len(repos)} repositories.")
        markdown_content = format_repos(repos)
        update_readme(markdown_content)
    else:
        print("No repositories found or an error occurred.")
