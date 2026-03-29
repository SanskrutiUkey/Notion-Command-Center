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
    print(f"{bot.user} online!")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    sender = str(message.author)
    msg_content = message.content

    params = {"sender": sender, "message": msg_content}
    url = f"{API_URL}/lead?{urlencode(params)}"

    try:
        response = requests.post(url, timeout=10)
        print(f"Forwarded: {msg_content}")
        print(f"Response: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")


bot.run(TOKEN)
