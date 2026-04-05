import discord
import requests
import os
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
API_URL = "https://notion-command-center.onrender.com"

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print(f"--- BOT STARTED ---")
    print(f"User: {bot.user}")
    print(f"Message Content Intent: {bot.intents.message_content}")
    print(f"-------------------")


@bot.event
async def on_message(message):
    # Log EVERY message for debugging
    print(f"DEBUG: Message from {message.author} in {message.channel}")
    print(f"DEBUG: Content: '{message.content}'")

    if message.author.bot:
        return

    sender = str(message.author)
    msg_content = message.content

    if not msg_content:
        print(
            "WARNING: Empty message content. Check 'Message Content Intent' in Discord Developer Portal."
        )
        return

    params = {"sender": sender, "message": msg_content}
    url = f"{API_URL}/lead?{urlencode(params)}"

    try:
        print(f"Sending to Render: {url}")
        response = requests.post(url, timeout=10)
        print(f"Forwarded: {msg_content}")
        print(f"Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error calling Render: {e}")


bot.run(TOKEN)
