import discord
import requests
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} online!')

@bot.event
async def on_message(message):
    if message.author.bot: return
    data = {"content": message.content, "author": {"username": str(message.author)}}
    requests.post(WEBHOOK_URL, json=data)
    print("Forwarded:", message.content)  # Debug

bot.run(TOKEN)