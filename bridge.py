import asyncio

import discord
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = discord.Client(intents=intents)


@bot.event
async def on_ready():
    print("Logged in successfully as: ", bot.user)

@bot.event
async def on_thread_create(thread: discord.Thread):
    channel_name = thread.parent.name

    thread_name = thread.name
    print("Title:", thread_name)

    parent_msg = await thread.parent.fetch_message(thread.id)
    if parent_msg.attachments:
        image_url = [a.url for a in parent_msg.attachments]
        print(image_url)

    # await asyncio.sleep(1.5)
    # starter = await thread.parent.fetch_message(thread.id)
    # print(starter)

bot.run(TOKEN)