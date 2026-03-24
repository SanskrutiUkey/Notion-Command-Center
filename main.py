from fastapi import FastAPI
from notion_client import Client
from dotenv import load_dotenv
import os
import re
import requests

load_dotenv()
app = FastAPI()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

INBOX_DB_ID = os.getenv("INBOX_DB_ID")
PRODUCT_KB_DB_ID = os.getenv("PRODUCT_KB_DB_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@app.get("/")
def root():
    return {"message": "Side Hustle Ops Engine ✅"}

@app.post("/lead")
async def create_lead(sender: str, message: str):
    # Create row in Inbox & Leads DB
    result = notion.pages.create(
        parent={"database_id": INBOX_DB_ID},
        properties={
            "Sender": {"email": sender},
            "Message": {"rich_text": [{"text": {"content": message}}]},
            "Status": {"status": {"name": "New"}},
        }
    )
    return {"Status": "Lead created ✅", "page_id": result["id"]}

@app.post("/discord-webhook")
async def discord_webhook(request: dict):
    message = request.get("content", "")
    sender = request.get("author", {}).get("username", "john@example.com")
    
    result = notion.pages.create(
        parent={"database_id": INBOX_DB_ID},
        properties={
            "Sender": {"email": sender},
            "Message": {"rich_text": [{"text": {"content": message}}]},
        }
    )
    return {"status": "✅ Row created", "page_id": result["id"]}

@app.post("/approve-send")
async def approve_send(page_id: str, sender: str, draft_reply: str):
    # Send to Discord via webhook
    payload = {
        "content": draft_reply,
        "username": "SideHustleOps Bot"
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)
    
    # Update Notion status
    notion.pages.update(
        page_id=page_id,
        properties={"Status": {"select": {"name": "Sent ✅"}}}
    )
    
    return {"status": "Sent ✅"}

@app.get("/ai-agent")
async def ai_agent():
    # 1. Find NEW rows in Inbox DB
    new_leads = notion.databases.query(
        database_id=INBOX_DB_ID,
        filter={"property": "Status", "status": {"equals": "New"}}
    )
    
    results = []
    for lead in new_leads['results']:
        sender = lead['properties']['Sender']['email']
        message = lead['properties']['Message']['rich_text'][0]['plain_text']
        
        # 2. Search Product KB for relevant info
        kb_results = notion.databases.query(
            database_id=PRODUCT_KB_DB_ID,
            filter={"property": "Tags", "multi_select": {"contains": "lead"}}
        )
        # Extract name from email (before @)

        name_match = re.search(r'^([^@]+)', sender)
        name = name_match.group(1).split()[0].capitalize() if name_match else "User"

        # 3. Mock AI reply (OpenAI later)
        kb_context = "Pricing: $29/mo + 14-day trial"
        draft = f"Hi {name}! {kb_context}. Let me know if you need setup help! 🚀"
        
        # 4. Update row with Draft Reply
        notion.pages.update(
            page_id=lead['id'],
            properties={
                "Draft Reply": {"rich_text": [{"text": {"content": draft}}]},
                "Status": {"status": {"name": "Ready"}}
            }
        )
        results.append(f"Processed {sender}")
    
    return {"processed": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)