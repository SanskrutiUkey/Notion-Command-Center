from fastapi import FastAPI
from notion_client import Client
from dotenv import load_dotenv
import os
import re
import requests
from fastapi import Request
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
async def discord_webhook(request: Request):  # Add Request import
    body = await request.json()
    message = body.get("content", "")
    sender = body.get("author", {}).get("username", "john@example.com")
    
    result = notion.pages.create(
        parent={"database_id": INBOX_DB_ID},
        properties={
            "Sender": {"email": sender},
            "Message": {"rich_text": [{"text": {"content": message}}]},
        }
    )
    return {"status": "✅ Row created", "page_id": result["id"]}

from pydantic import BaseModel

class ApproveRequest(BaseModel):
    page_id: str
    sender: str
    draft_reply: str


@app.post("/approve-send")
async def approve_send(data: ApproveRequest):
    # Send to Discord via webhook
    page_id = data.page_id
    sender = data.sender
    draft_reply = data.draft_reply
    
    notion.pages.update(page_id=page_id, archived=False)

    requests.post(DISCORD_WEBHOOK_URL, json={"content": draft_reply})
    
    # Update Notion status
    notion.pages.update(
        page_id=page_id,
        properties={"Status": {"status": {"name": "Sent"}}}
    )
    
    return {"status": "Sent ✅"}

@app.head("/ai-agent")
async def ai_agent():
    new_leads = notion.databases.query(
        database_id=INBOX_DB_ID,
        filter={"property": "Status", "status": {"equals": "New"}}
    )
    
    results = []
    for lead in new_leads['results']:
        sender_prop = lead['properties']['Sender']
        if 'email' in sender_prop:
            sender = sender_prop['email']
            name = sender.split('@')[0].capitalize()
        elif 'title' in sender_prop and sender_prop['title']:
            sender = sender_prop['title'][0]['plain_text']
            name = sender.split()[0].capitalize()
        else:
            sender = "user@example.com"
            name = "User"

        import re
        name = re.search(r'^([^@]+)', sender).group(1).split()[0].capitalize()
        
        message = lead['properties']['Message']['rich_text'][0]['plain_text']
        
        # MCP: Search Product KB for context
        kb_search = notion.databases.query(
            database_id=PRODUCT_KB_DB_ID,
            filter={
                "or": [
                    {"property": "Tags", "multi_select": {"contains": "Lead"}},
                    {"property": "Tags", "multi_select": {"contains": "Pricing"}}, 
                    {"property": "Tags", "multi_select": {"contains": "Setup"}},
                    {"property": "Tags", "multi_select": {"contains": "Features"}},
                    {"property": "Tags", "multi_select": {"contains": "Support"}}
                ]
            }
        )
        
        kb_context = []
        for kb in kb_search['results'][:3]:
            content_prop = kb['properties'].get('Content', {})
            if content_prop.get('rich_text') and content_prop['rich_text']:
                kb_context.append(content_prop['rich_text'][0]['plain_text'])
            else:
                kb_context.append("No content found")
        
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://openrouter.ai/api/v1")
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
                "Kb Links": {"url": kb_urls[0] if kb_urls else "https://notion.so/your-kb"},  # Link to KB
                "Status": {"status": {"name": "Ready"}}
            }
        )
        results.append(f"AI replied to {name}")
    
    return {"processed": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)