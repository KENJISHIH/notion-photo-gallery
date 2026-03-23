"""
fetch_notion.py
從 Notion 資料庫抓取「家族旅行」標籤的相簿資料
只取 4 個欄位：相簿名稱、相簿連結（Google）、標籤、相簿日期
輸出：albums.json
"""

import os
import json
import urllib.request
import urllib.error

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ["NOTION_DATABASE_ID"]  # 相簿資料庫 ID

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

FILTER = {
    "filter": {
        "property": "標籤",
        "multi_select": {
            "contains": "家族旅行"
        }
    },
    "sorts": [
        {
            "property": "相簿日期",
            "direction": "descending"
        }
    ]
}


def notion_request(url, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST" if data else "GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_all_pages():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    results = []
    payload = dict(FILTER)
    payload["page_size"] = 100

    while True:
        resp = notion_request(url, payload)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        payload["start_cursor"] = resp["next_cursor"]

    return results


def extract_fields(page):
    props = page.get("properties", {})

    # 相簿名稱（title 欄位）
    title_list = props.get("相簿名稱", {}).get("title", [])
    name = "".join(t.get("plain_text", "") for t in title_list).strip()

    # 相簿連結（url 欄位）
    album_url = props.get("相簿連結", {}).get("url") or ""

    # 只保留 Google 相關連結
    if album_url and not ("google" in album_url or "goo.gl" in album_url):
        album_url = ""

    # 標籤（multi_select）
    tags = [t["name"] for t in props.get("標籤", {}).get("multi_select", [])]

    # 相簿日期
    date_obj = props.get("相簿日期", {}).get("date") or {}
    date = date_obj.get("start", "")

    return {
        "name": name,
        "url": album_url,
        "tags": tags,
        "date": date,
        "notion_id": page["id"],
    }


def main():
    print("🔍 從 Notion 抓取「家族旅行」相簿...")
    pages = fetch_all_pages()
    print(f"   找到 {len(pages)} 筆")

    albums = [extract_fields(p) for p in pages]
    # 過濾掉沒有名稱的頁面
    albums = [a for a in albums if a["name"]]

    output = {"albums": albums, "total": len(albums)}
    with open("albums.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"✅ 輸出 albums.json，共 {len(albums)} 筆")


if __name__ == "__main__":
    main()
