import sqlite3
import time
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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    repos_data = []
    page = 1

    print("全体スクレイピングを開始します")

    while True:
        url = f"{base_url}?page={page}"
        print(f"--- ページ {page} を取得中: {url} ---")

        time.sleep(1)
        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            print(f"アクセス制限またはエラーが発生しました (ステータスコード: {response.status_code})")
            break

        soup = BeautifulSoup(response.text, 'html.parser')

        repo_list = soup.find_all('li', class_=lambda x: x and ('Box-row' in x or 'ListItem' in x))

        if not repo_list:
            print("これ以上のリポジトリが見つからないため、スクレイピングを終了します。")
            break

        found_in_page = 0
        for repo in repo_list:
            name_tag = repo.find('a', itemprop='name codeRepository') or repo.find('a', href=lambda x: x and x.startswith('/google/') and x.count('/') == 2)
            if not name_tag:
                continue
            repo_name = name_tag.text.strip()

            lang_tag = repo.find('span', itemprop='programmingLanguage')
            language = lang_tag.text.strip() if lang_tag else "N/A"

            star_tag = repo.find('a', href=lambda x: x and x.endswith('/stargazers'))
            stars = star_tag.text.strip() if star_tag else "0"

            repos_data.append((repo_name, language, stars))
            found_in_page += 1

        print(f"ページ {page}: {found_in_page} 件取得（累計: {len(repos_data)} 件）")

        if found_in_page == 0:
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

def display_stored_data(db_name="github_google_repos.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    print("\n=== 保存されたデータ (SELECT文の実行結果) ===")
    cursor.execute("SELECT id, repo_name, language, stars FROM repositories")
    rows = cursor.fetchall()

    for row in rows:
        print(f"ID: {row[0]} | リポジトリ名: {row[1]} | 言語: {row[2]} | スター数: {row[3]}")

    print(f"\n総レコード数: {len(rows)} 件")
    conn.close()

if __name__ == "__main__":
    DB_NAME = "github_google_repos.db"
    
    init_db(DB_NAME)
    
    scraped_data = scrape_all_github_google()
    
    if scraped_data:
        save_to_db(scraped_data, DB_NAME)
        display_stored_data(DB_NAME)