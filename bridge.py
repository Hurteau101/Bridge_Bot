import asyncio
from datetime import datetime, timezone
import aiohttp
import discord
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
ALLOWED_CHANNEL_IDS = os.getenv("ALLOWED_CHANNEL_IDS")
ERROR_BOT_WEBHOOK = os.getenv("ERROR_BOT_WEBHOOK")

BASE_URL = "https://externalapi.pikkit.com/v1/quickpick"

if not all([TOKEN, API_KEY, ALLOWED_CHANNEL_IDS, ERROR_BOT_WEBHOOK]):
    raise Exception("Missing environment variables")


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
session: aiohttp.ClientSession | None = None
bot = discord.Client(intents=intents)
active_requests = set()

@bot.event
async def on_ready():
    global session
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30)
    )
    print("Logged in successfully as: ", bot.user)

async def send_error_notification(text: str, session: aiohttp.ClientSession, thread_id: int):
    payload = {
        "embeds": [
            {
                "title": "QuickPick Error",
                "description": text,
                "color": 16711680,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "footer": {
                    "text": "QuickPick Error Monitor"
                }
            }
        ]
    }

    async with session.post(
        ERROR_BOT_WEBHOOK,
        json=payload
    ) as response:
        if response.status != 204:
            print(f"Error sending notification: {response.status}")

    active_requests.discard(thread_id)

async def create_betslip(text: str, images: list, session: aiohttp.ClientSession) -> str | None:
    payload = {
        "text": text,
        "images": images
    }

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        async with session.post(
                url=f"{BASE_URL}/create",
                json=payload,
                headers=headers
        ) as response:

            if response.status != 200:
                return None

            data = await response.json()
            return data.get("request_id")

    except aiohttp.ClientError:
        return None

async def poll_status(request_id: str, session: aiohttp.ClientSession) -> dict:
    for _ in range(90):
        await asyncio.sleep(3)

        try:
            async with session.get(
                    url=f"{BASE_URL}/status?request_id={request_id}",
                    headers={"X-API-Key": API_KEY}
            ) as response:

                if response.status != 200:
                    return {"status": "error", "message": f"Error: {response.status}"}

                data = await response.json()

        except aiohttp.ClientError as e:
            return {"status": "error", "message": str(e)}

        if data.get("status") == "complete":
            link = data.get("link")

            if not link:
                return {"status": "error", "message": "No link found"}

            return {
                "status": "success",
                "message": link
            }

    return {"status": "error", "message": "Timeout"}


async def handle_polling(thread, request_id, session, placeholder):
    link = await poll_status(request_id, session)
    if link.get("status") != "success":
        await remove_placeholder(placeholder)
        await thread.send("Error Generating QuickPick Link")
        await send_error_notification(link.get("message"), session, thread.id)
        return

    await remove_placeholder(placeholder)

    try:
        await thread.send(link["message"])
    except discord.NotFound:
        pass
    finally:
        active_requests.discard(thread.id)



async def remove_placeholder(placeholder):
    try:
        await placeholder.delete()
    except discord.NotFound:
        return


@bot.event
async def on_thread_create(thread: discord.Thread):
    global session

    if session is None or not thread.parent:
        return

    channel_id = thread.parent.id

    channel_ids = [
        int(channel_id)
        for channel_id in ALLOWED_CHANNEL_IDS.split(',')
    ]

    if channel_id not in channel_ids or thread.id in active_requests:
        return

    active_requests.add(thread.id)

    await asyncio.sleep(1)

    try:
        parent_message = await thread.parent.fetch_message(thread.id)
    except discord.NotFound:
        active_requests.discard(thread.id)
        return

    thread_text = thread.name

    images = [
        attachment.url
        for attachment in parent_message.attachments
    ]

    placeholder = await thread.send("Generating QuickPick Link. Please wait..")

    try:
        request_id = await create_betslip(thread_text, images, session)
    except Exception as e:
        await remove_placeholder(placeholder)
        await thread.send("Error Generating QuickPick Link")
        await send_error_notification(str(e), session, thread.id)
        return

    if not request_id:
        await remove_placeholder(placeholder)
        await thread.send("Error Generating QuickPick Link")
        await send_error_notification("No request ID returned from API\n\n"
                                      f"**Text**\n```{thread_text}```\n"
                                      f"**Images**\n" + "\n".join(images), session, thread.id)
        return

    asyncio.create_task(handle_polling(thread, request_id, session, placeholder))


bot.run(TOKEN)