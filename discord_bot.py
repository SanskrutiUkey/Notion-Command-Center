import discord
import requests
from dotenv import load_dotenv
import os

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} logged in!')

@bot.event
async def on_message(message):
    if message.author.bot: return
    data = {
        "content": message.content, 
        "author": {"username": str(message.author)}
    }
    requests.post(WEBHOOK_URL, json=data)

bot.run(DISCORD_TOKEN)