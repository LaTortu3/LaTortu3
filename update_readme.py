import os
import re
import requests

def get_repos(username, token):
    all_repos = []
    page = 1

    url_base = f"https://api.github.com/user/repos?visibility=all&per_page=100"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    if not token:
        url_base = f"https://api.github.com/users/{username}/repos?per_page=100"
        headers = {"Accept": "application/vnd.github.v3+json"}

    while True:
        url = f"{url_base}&page={page}" if "?" in url_base else f"{url_base}?page={page}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        repos = response.json()
        if not repos:
            break

        all_repos.extend(repos)

        # If we got less than 100, it's the last page
        if len(repos) < 100:
            break

        page += 1

    return all_repos

def get_recent_commits(username, repo_name, token):
    url = f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=3"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    if not token:
         url = f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=3"
         headers = {"Accept": "application/vnd.github.v3+json"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def get_languages(username, repo_name, token):
    url = f"https://api.github.com/repos/{username}/{repo_name}/languages"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    if not token:
        url = f"https://api.github.com/repos/{username}/{repo_name}/languages"
        headers = {"Accept": "application/vnd.github.v3+json"}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return {}

def format_repo(repo, commits, languages):
    name = repo['name']
    url = repo['html_url']
    stars = repo['stargazers_count']
    description = repo['description'] or "No description provided."
    is_private = repo['private']

    badge = "🔒 Private" if is_private else "🌍 Public"

    lang_str = ", ".join(languages.keys()) if languages else "Not specified"

    markdown = f"#### [{name}]({url}) - {badge} - ⭐ {stars}\n"
    markdown += f"> {description}\n\n"
    markdown += f"**Tech Stack / Languages:** {lang_str}\n\n"

    if commits:
        markdown += "**Recent Commits:**\n"
        for commit in commits:
            msg = commit['commit']['message'].split('\n')[0]
            date = commit['commit']['author']['date'][:10]
            sha = commit['sha'][:7]
            commit_url = commit['html_url']
            markdown += f"- [`{sha}`]({commit_url}) {date} - {msg}\n"
    else:
        markdown += "*No recent commits found.*\n"

    return markdown + "\n"

def update_readme(markdown_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    # Regex to find the markers and replace the content between them
    pattern = r"(<!-- DYNAMIC_REPOS_START -->)(.*?)(<!-- DYNAMIC_REPOS_END -->)"

    # Check if markers exist
    if not re.search(pattern, readme_content, re.DOTALL):
        print("Markers not found in README.md")
        return

    new_content = re.sub(pattern, f"\\1\n{markdown_content}\n\\3", readme_content, flags=re.DOTALL)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_content)

def main():
    username = "LaTortu3" # You can hardcode this or pass it via env
    token = os.environ.get("GH_TOKEN")

    try:
        repos = get_repos(username, token)

        # Sort repos by stars
        repos = sorted(repos, key=lambda x: x['stargazers_count'], reverse=True)

        full_markdown = ""
        for repo in repos:
            # Skip forks if you want, or include them
            if repo['fork']:
                continue

            owner = repo['owner']['login'] # Handles case if the user has access to org repos

            print(f"Fetching details for {repo['name']}...")
            commits = get_recent_commits(owner, repo['name'], token)
            languages = get_languages(owner, repo['name'], token)

            full_markdown += format_repo(repo, commits, languages)

        update_readme(full_markdown)
        print("README updated successfully!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
