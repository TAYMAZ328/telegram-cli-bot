from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityMentionName

from dotenv import load_dotenv
import os, asyncio

from util import authorize, sleep_timer, log_error
from config import boss_id, user1



load_dotenv()
api_hash = os.getenv("API_HASH")
api_id = os.getenv("API_ID")

client = TelegramClient('tg', api_id, api_hash)


@client.on(events.NewMessage(pattern=r"/getinfo\s*(@?\w+)?"))
async def get_id(event, d=False):
    if not authorize(event): return

    try:
        par = event.pattern_match.group(1)
        id = None

        if event.is_reply:
            msg = await event.get_reply_message()
            user = await msg.get_sender()
            id = user.id

        elif event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntityMentionName):
                    id = entity.user_id
                    break

        if not id:
            if par and par.startswith("@"): id = par
            elif par and par.isdigit(): id = int(par)
            else: return await event.reply("No valid user found")

        user = await client.get_entity(id)
        if d: return user

        await event.reply(f"User: `{user.first_name} {user.last_name or ""}`\nID: `{user.id}`\nUsername: {f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"}\nPhone Number: {f"+{user.phone}" if user.phone else "Hiden"}\n"
                        f"Self: {user.is_self}\nPremium: {user.premium}\nVerified: {user.verified}\nRestricted: {user.restricted}  | Reason: {user.restriction_reason or "None"}\nStatus: {type(user.status).__name__}\nLanguage: {user.lang_code or "Not specified"}", parse_mode='md')
    
    except Exception as e:
        log_error(f"{event.text}\n{e}") 
        await event.reply("Couldn't retrieve user info")


@client.on(events.NewMessage(pattern="/reset"))
async def reset(event):
    if not authorize(event): return

    user1.boss = [boss_id]
    user1.enemy = []
    user1.sens = []
    user1.delay = (2,7)
    user1.active = True
    user1.replied = True
    user1.evil = False
    user1.lvl = [None, None, "off"]
    user1.last_msg = {}
    user1.sleep_task = None
    await event.reply(f"All Setting has been reset to defaults.")


@client.on(events.NewMessage(pattern=r"/sleep\s*(\d+)?"))
async def sleep(event):
    if not authorize(event, opt=True): return

    if user1.active:
        # Cancel any existing sleep task
        if user1.sleep_task and not user1.sleep_task.done():
            user1.sleep_task.cancel()
        timer = event.pattern_match.group(1)
        if timer:
            timer = int(timer)
            user1.active = False
            # Create new sleep task
            user1.sleep_task = asyncio.create_task(sleep_timer(timer, event))
            await event.reply(f"Entered Sleep Mode for {timer} sec.")
        else:
            user1.active = False
            await event.reply("Sleep Mode Activated\nUse /run to Wake up")
    else:
        await event.reply("Sleep Mode is already Activated")


@client.on(events.NewMessage(pattern="/run"))
async def wake(event):
    if not authorize(event, opt=True): return

    if not user1.active:
        user1.active = True
        if user1.sleep_task and not user1.sleep_task.done():
            user1.sleep_task.cancel()
        await event.reply("Sleep Mode Cancelled")
    else:
        await event.reply("Running already")


@client.on(events.NewMessage(pattern="/kill"))
async def shutdown(event):
    if not authorize(event): return

    await event.reply("Shutting down completely...")
    await client.disconnect()
    os._exit(0)

@client.on(events.NewMessage(pattern="/backup"))
async def backup(event):
    if not authorize(event): return

    await event.respond("Backup proccess starting...")


@client.on(events.NewMessage(pattern="/help"))
async def help(event):
    if authorize(event):
        await event.respond("""Commands:
/add [ username | ID | reply | tag ] - Add an enemy.
/del [ username | ID | reply | tag ] - Remove an enemy.
/enemies - Show the list of all enemies.
/spam [num] - Repeatedly repost the replied-to message a specified number of times.
/forcerep - Toggle Reply Mode
/evilmode - Toggle Evil Mode. When activated, the bot will automatically reply to enemies using their last message.
/settime [off | n-m] - Schedule a delay interval
/setlevel [off | 1 | 2 | 3] - Set the bot's intensity level, (Leave empty to check current level)
/acmd [ username | ID | reply | tag ]:optional - Add a user as a Commander
/dcmd [ username | ID | reply | tag ]:optional - Remove a user from the Commander list.
/cmds - Show the list of current Commanders.
/sleep [time]:optional - Toggle Sleep Mode
/run - Verify system status or Cancel Sleep Mode
/kill - Shut Down the system permanently
/reset - Reset all settings to default
/save [ message link | reply ] - Archive a message
/cvm -  Convert the replied message into a video note
/rep [message link] [ message link | reply ]:optional - Reply to a message(first-parameter) with a message(second-parameter or reply)
/getinfo [ username | ID | reply | tag ] - Retrieve user information.
/cleanup [group username] [limit]:optional [offset(use \" - \" from oldest)]:optional - Delete messages in a specific group.
Note: Due to Telegram policy and the risk of Floodwait, the deletion limit is set to 2000 by default.
/backup [chat ID]:optional - Back Up from all of the Channels, Groups, Chats and Bots, or from specific chat messages, (Updating...)
/help - Commands guide
""", parse_mode='md')

