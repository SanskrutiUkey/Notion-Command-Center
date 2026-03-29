import discord
import requests
import os
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
    response = requests.post(f"{API_URL}/lead?sender={sender}&message={msg_content}")
    print(f"Forwarded: {msg_content} - Response: {response.status_code}")


bot.run(TOKEN)
