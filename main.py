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
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    session = requests.Session()
    session.headers.update(headers)

    repos_data = []
    seen_repos = set()

    queries = [
        "", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
        "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "-", "_"
    ]

    print("全件スクレイピングを開始します...")

    for q in queries:
        page = 1
        zero_new_streak = 0 

        while True:
            if q == "":
                url = f"{base_url}?page={page}"
            else:
                url = f"{base_url}?q={q}&page={page}"

            print(f"--- 取得中 (フィルタ='{q}', ページ={page}): {url} ---")
            
            time.sleep(1)

            try:
                response = session.get(url, timeout=15)
            except Exception as e:
                print(f"通信が一時切断されました。10秒待機して再試行します... ({e})")
                time.sleep(10)
                continue

            if response.status_code == 429:
                print("アクセス制限(429)のため15秒待機して再試行します...")
                time.sleep(15)
                continue
            elif response.status_code != 200:
                print(f"ページ取得終了 (ステータスコード: {response.status_code})")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            all_links = soup.find_all('a')

            items_on_page = 0
            new_in_page = 0

            for link in all_links:
                href = link.get('href', '')

                if not href.startswith('/google/') or href.count('/') != 2:
                    continue

                repo_name = href.split('/')[-1]

                if repo_name in ['repositories', 'people', 'projects', 'packages', 'teams', 'sponsors']:
                    continue

                container = link.find_parent('li')
                if not container and link.parent:
                    container = link.parent.parent
                if not container:
                    continue

                star_tag = container.find('a', href=f"{href}/stargazers")
                if not star_tag:
                    continue

                items_on_page += 1

                if repo_name in seen_repos:
                    continue

                stars = star_tag.text.strip()

                lang_tag = container.find('span', itemprop='programmingLanguage')
                if not lang_tag:
                    for span in container.find_all('span'):
                        classes = span.get('class', [])
                        if 'repo-language-color' in classes and span.parent:
                            lang_tag = span.parent
                            break

                language = lang_tag.text.strip() if lang_tag else "N/A"

                seen_repos.add(repo_name)
                repos_data.append((repo_name, language, stars))
                new_in_page += 1

            print(f"新規取得: {new_in_page} 件 / ページ内: {items_on_page} 件（累計: {len(repos_data)} 件）")

            if items_on_page == 0:
                break

            # 新規取得0件が3ページ連続したら、すでに取得済みの領域なので次のフィルタへ進む
            if new_in_page == 0:
                zero_new_streak += 1
                if zero_new_streak >= 3:
                    print(f"フィルタ='{q}' の新規データ取得が完了したため次へ進みます。")
                    break
            else:
                zero_new_streak = 0

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