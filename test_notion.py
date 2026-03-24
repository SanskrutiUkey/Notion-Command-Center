import requests
import os

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
INBOX_DB_ID = os.getenv("INBOX_DB_ID")

url = f"https://api.notion.com/v1/databases/{INBOX_DB_ID}/query"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, json={})

if response.status_code == 200:
    results = response.json()
    print(f"✅ Success! Found {len(results['results'])} rows")
    print(results)
else:
    print(f"❌ Error {response.status_code}: {response.text}")