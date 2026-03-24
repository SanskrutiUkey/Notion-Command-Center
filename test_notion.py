import requests

NOTION_TOKEN = "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"
INBOX_DB_ID = "323575f982e28026a110f564087b32b6"

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