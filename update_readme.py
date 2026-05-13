import os
import re
import requests

GITHUB_TOKEN = os.getenv("GH_TOKEN")
HEADERS = {}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"token {GITHUB_TOKEN}"

def fetch_repos():
    if GITHUB_TOKEN:
        # Fetch user's repos including private ones
        url = "https://api.github.com/user/repos?affiliation=owner&sort=updated&per_page=100"
    else:
        # Fallback to public repos if token is not available
        url = "https://api.github.com/users/LaTortu3/repos?sort=updated&per_page=100"

    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def fetch_latest_commit(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/commits"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        commits = response.json()
        if commits and len(commits) > 0:
            return commits[0]['commit']['message'].split('\n')[0]
    return "No commits found"

def fetch_languages(repo_full_name):
    url = f"https://api.github.com/repos/{repo_full_name}/languages"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return list(response.json().keys())
    return []

def generate_markdown(repos):
    markdown = ""
    for repo in repos:
        name = repo.get("name", "Unknown")
        html_url = repo.get("html_url", "#")
        description = repo.get("description") or "No description provided."
        stars = repo.get("stargazers_count", 0)
        is_private = repo.get("private", False)
        repo_full_name = repo.get("full_name")

        # Fetch additional details
        latest_commit_msg = fetch_latest_commit(repo_full_name)
        languages = fetch_languages(repo_full_name)

        # Formatting
        visibility = "🔒 Private" if is_private else "🌐 Public"
        language_str = ", ".join(languages) if languages else "Not specified"

        markdown += f"#### [{name}]({html_url}) {visibility}\n"
        markdown += f"> {description}\n\n"
        markdown += f"- ⭐ **Stars:** {stars}\n"
        markdown += f"- 🛠 **Tech/Skills:** {language_str}\n"
        markdown += f"- 📝 **Latest Commit:** `{latest_commit_msg}`\n\n"

    return markdown

def update_readme(markdown_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_text = f.read()

    # Use regex to find and replace the content between markers
    pattern = r"(<!-- DYNAMIC_REPOS_START -->\n)(.*?)(\n<!-- DYNAMIC_REPOS_END -->)"

    # We use re.DOTALL so that '.' matches newlines
    new_readme_text = re.sub(pattern, r"\g<1>" + markdown_content.strip() + r"\g<3>", readme_text, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme_text)

if __name__ == "__main__":
    repos = fetch_repos()
    print(f"Fetched {len(repos)} repositories.")
    markdown_content = generate_markdown(repos)
    print("Generated markdown length:", len(markdown_content))
    update_readme(markdown_content)
    print("README.md updated successfully.")
