from fastapi import FastAPI
from notion_client import Client
from dotenv import load_dotenv
import os
import re
import requests
from openai import OpenAI

load_dotenv()
app = FastAPI()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

INBOX_DB_ID = os.getenv("INBOX_DB_ID")
PRODUCT_KB_DB_ID = os.getenv("PRODUCT_KB_DB_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_KEY)

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
        properties={"Status": {"status": {"name": "Sent ✅"}}}
    )
    
    return {"status": "Sent ✅"}

@app.get("/ai-agent")
async def ai_agent():
    new_leads = notion.databases.query(
        database_id=INBOX_DB_ID,
        filter={"property": "Status", "select": {"equals": "New"}}
    )
    
    results = []
    for lead in new_leads['results']:
        sender = lead['properties']['Sender']['title'][0]['plain_text']
        import re
        name = re.search(r'^([^@]+)', sender).group(1).split()[0].capitalize()
        
        message = lead['properties']['Message']['rich_text'][0]['plain_text']
        
        # MCP: Search Product KB for context
        kb_search = notion.databases.query(
            database_id=PRODUCT_KB_DB_ID,
            filter={
                "or": [
                    {"property": "Tags", "multi_select": {"contains": "lead"}},
                    {"property": "Tags", "multi_select": {"contains": "pricing"}}, 
                    {"property": "Tags", "multi_select": {"contains": "setup"}},
                    {"property": "Tags", "multi_select": {"contains": "features"}},
                    {"property": "Tags", "multi_select": {"contains": "support"}}
                ]
            }
        )
        
        kb_context = []
        for kb in kb_search['results'][:3]:  # Top 3 matches
            kb_context.append(kb['properties']['Content']['rich_text'][0]['plain_text'])
        
        # OpenAI generates reply
        prompt = f"""User asked: "{message}"
Search Product KB for relevant info: {kb_context}

Generate reply:
- Match USER question exactly (pricing, setup, features)
- Use ONLY KB context  
- Friendly, <80 words
- Sign off: "Ask me anything! 🚀" """
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        draft = response.choices[0].message.content
        
        # Update Notion row
        kb_urls = [kb['url'] for kb in kb_search['results'][:3]]

        notion.pages.update(
            page_id=lead['id'],
            properties={
                "Draft Reply": {"rich_text": [{"text": {"content": draft}}]},
                "KB Links": {"url": kb_urls[0] if kb_urls else "https://notion.so/your-kb"},  # Link to KB
                "Status": {"select": {"name": "Ready"}}
            }
        )
        results.append(f"AI replied to {name}")
    
    return {"processed": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)