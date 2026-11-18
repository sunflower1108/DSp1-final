import sqlite3
import time
import re
import requests
from bs4 import BeautifulSoup

def init_db(db_name="github_google_repos.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_name TEXT UNIQUE,
            language TEXT,
            stars TEXT
        )
    ''')
    conn.commit()
    conn.close()

def scrape_all_github_google():
    base_url = "https://github.com/orgs/google/repositories"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    repos_data = []
    seen_repos = set()
    page = 1

    print("全件スクレイピングを開始します...")

    while True:
        url = f"{base_url}?page={page}"
        print(f"--- ページ {page} を取得中: {url} ---")
        
        time.sleep(0.1)
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"アクセス制限またはエラーが発生しました (ステータスコード: {response.status_code})")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        repo_links = soup.find_all('a', href=re.compile(r'^/google/[^/]+$'))

        found_in_page = 0
        for link in repo_links:
            href = link.get('href', '')
            repo_name = href.split('/')[-1]

            if repo_name in ['repositories', 'people', 'projects', 'packages', 'teams', 'sponsors'] or repo_name in seen_repos:
                continue

            container = link.find_parent('li') or link.find_parent('div', class_=re.compile(r'Box|ListItem|repo|row', re.I))
            if not container:
                container = link.parent.parent if link.parent else None

            if not container:
                continue

            star_tag = container.find('a', href=f"{href}/stargazers")
            if not star_tag:
                continue

            stars = star_tag.text.strip()

            lang_tag = container.find('span', itemprop='programmingLanguage')
            if not lang_tag:
                lang_color = container.find('span', class_=re.compile(r'repo-language-color'))
                if lang_color and lang_color.parent:
                    lang_tag = lang_color.parent

            language = lang_tag.text.strip() if lang_tag else "N/A"

            seen_repos.add(repo_name)
            repos_data.append((repo_name, language, stars))
            found_in_page += 1

        print(f"ページ {page}: {found_in_page} 件取得（累計: {len(repos_data)} 件）")

        if found_in_page == 0:
            print("これ以上のリポジトリが見つからないため、スクレイピングを終了します。")
            break

        page += 1

    return repos_data

def save_to_db(data, db_name="github_google_repos.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    for item in data:
        cursor.execute('''
            INSERT OR REPLACE INTO repositories (repo_name, language, stars)
            VALUES (?, ?, ?)
        ''', item)

    conn.commit()
    conn.close()
    print(f"\n合計 {len(data)} 件のデータをデータベースに保存しました。")

def display_stored_data(db_name="github_google_repos.db", output_file="result.txt"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    cursor.execute("SELECT id, repo_name, language, stars FROM repositories")
    rows = cursor.fetchall()

    with open(output_file, "w", encoding="utf-8") as f:
        header = "=== 保存されたデータ (SELECT文の実行結果) ==="
        print("\n" + header)
        f.write(header + "\n")  

        for row in rows:
            line = f"ID: {row[0]} | リポジトリ名: {row[1]} | 言語: {row[2]} | スター数: {row[3]}"
            print(line)
            f.write(line + "\n")

        footer = f"\n総レコード数: {len(rows)} 件"
        print(footer)
        f.write(footer + "\n")

    conn.close()
    print(f"実行結果を {output_file} に保存しました。")

if __name__ == "__main__":
    DB_NAME = "github_google_repos.db"
    
    init_db(DB_NAME)
    scraped_data = scrape_all_github_google()
    
    if scraped_data:
        save_to_db(scraped_data, DB_NAME)
        display_stored_data(DB_NAME)