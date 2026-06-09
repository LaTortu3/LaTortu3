import os
import requests
import re

GITHUB_TOKEN = os.getenv("GH_TOKEN")
GRAPHQL_URL = "https://api.github.com/graphql"

def fetch_repos():
    query = """
    {
      viewer {
        repositories(first: 100, orderBy: {field: PUSHED_AT, direction: DESC}) {
          nodes {
            name
            url
            isPrivate
            stargazerCount
            primaryLanguage {
              name
            }
            defaultBranchRef {
              target {
                ... on Commit {
                  history(first: 3) {
                    edges {
                      node {
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
    }
    """
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(GRAPHQL_URL, json={'query': query}, headers=headers)
    if response.status_code == 200:
        return response.json()['data']['viewer']['repositories']['nodes']
    else:
        raise Exception(f"Query failed to run by returning code of {response.status_code}. {response.text}")

def format_repos_html(repos):
    html = ""
    for repo in repos:
        name = repo['name']
        url = repo['url']
        is_private = "🔒 Privé" if repo['isPrivate'] else "🌍 Public"
        stars = repo['stargazerCount']
        language = repo['primaryLanguage']['name'] if repo['primaryLanguage'] else "N/A"

        html += f"<details>\n"
        html += f"<summary><b><a href='{url}'>{name}</a></b> - {is_private} | ⭐️ {stars} | 💻 {language}</summary>\n\n"
        html += f"<ul>\n"

        if repo.get('defaultBranchRef') and repo['defaultBranchRef'].get('target') and repo['defaultBranchRef']['target'].get('history'):
            commits = repo['defaultBranchRef']['target']['history']['edges']
            for commit_edge in commits:
                commit = commit_edge['node']
                date = commit['committedDate'][:10]
                message = commit['messageHeadline']
                html += f"<li><i>{date}</i> : {message}</li>\n"
        else:
             html += f"<li>Aucun commit trouvé.</li>\n"

        html += f"</ul>\n"
        html += f"</details>\n\n"

    return html

def update_readme(new_content):
    with open("README.md", "r", encoding="utf-8") as f:
        readme_content = f.read()

    pattern = re.compile(r"(<!-- DYNAMIC_REPOS_START -->\n).*?(<!-- DYNAMIC_REPOS_END -->)", re.DOTALL)
    updated_content = pattern.sub(rf"\g<1>{new_content}\n\g<2>", readme_content)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(updated_content)

def get_mock_repos():
    return [
        {
            "name": "SuperJeu_Unreal",
            "url": "https://github.com/LaTortu3/SuperJeu_Unreal",
            "isPrivate": False,
            "stargazerCount": 42,
            "primaryLanguage": {"name": "C++"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Ajout du système de combat", "committedDate": "2024-05-12T10:00:00Z"}},
                            {"node": {"messageHeadline": "Correction bug collision", "committedDate": "2024-05-10T14:30:00Z"}},
                            {"node": {"messageHeadline": "Initial commit", "committedDate": "2024-05-01T08:00:00Z"}}
                        ]
                    }
                }
            }
        },
        {
            "name": "Auto_Scripts",
            "url": "https://github.com/LaTortu3/Auto_Scripts",
            "isPrivate": True,
            "stargazerCount": 5,
            "primaryLanguage": {"name": "Python"},
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "edges": [
                            {"node": {"messageHeadline": "Update update_readme.py", "committedDate": "2024-06-08T18:20:00Z"}},
                            {"node": {"messageHeadline": "Add GraphQL query", "committedDate": "2024-06-07T09:15:00Z"}}
                        ]
                    }
                }
            }
        }
    ]

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        if os.getenv("GITHUB_ACTIONS") == "true":
            raise Exception("Erreur critique : GH_TOKEN est manquant dans l'environnement GitHub Actions !")
        else:
            print("⚠️ GH_TOKEN introuvable. Utilisation des données fictives (mock data) pour les tests locaux.")
            repos = get_mock_repos()
    else:
        print("✅ GH_TOKEN trouvé. Récupération des données depuis GitHub API...")
        repos = fetch_repos()

    html_content = format_repos_html(repos)
    update_readme(html_content)
    print("README mis à jour avec succès !")
