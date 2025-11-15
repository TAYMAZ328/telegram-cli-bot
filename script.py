from telethon import TelegramClient, events
from telethon.tl.types import MessageEntityMentionName
from telethon.errors import FloodWaitError

import csv, logging, os, subprocess, asyncio
from random import choice, randint, uniform
from moviepy import VideoFileClip
from datetime import datetime


def get_token():
    with open("token.csv", "r") as f:
        c = csv.reader(f)
        return list(c)[0]

api_hash, api_id, boss_id = get_token()
boss_id = int(boss_id)

client = TelegramClient('tg', api_id, api_hash)


class UserConfig:
    boss = [boss_id]
    enemy = []
    delay = (2,7)
    active = True
    replied= True
    sleep_task = None
    sens = []
user1 = UserConfig()


@client.on(events.NewMessage())
async def handler(event):
    if user1.active:
        sender = int(event.sender_id)
        if sender in user1.boss: return 
        if sender in user1.enemy and eval("event.is_reply if user1.replied else True"):
            async with client.action(event.chat_id, 'typing'):
                delay = user1.delay
                if delay != 'off':
                    await asyncio.sleep(uniform(delay[0],delay[1]))
                await event.reply(choose())


@client.on(events.NewMessage(pattern=r"/add\s*(?:(.+))?"))
async def add_enemy(event):
    if not authorize(event): return

    user = await get_id(event, d=True)
    id = int(user.id)
    try:
        if id in user1.enemy:
            raise ValueError
        if not id or id in user1.boss:
            raise Exception

        user1.enemy.append(id)
        await event.respond(f"Enemy [{id}] added.")
    except ValueError:
        await event.respond(f"User is already added")
    except Exception:
        await event.respond(f"Couldn't add user.")


@client.on(events.NewMessage(pattern=r"/del\s*(?:(.+))?"))
async def add_enemy(event):
    if not authorize(event): return
       
    user = await get_id(event, d=True)
    id = int(user.id)
    try:
        if id not in user1.enemy:
            raise ValueError

        user1.enemy.remove(id)
        await event.respond(f"Enemy [{id}] removed.")
    except ValueError:
        await event.respond(f"User does not exist in the Enemy List")
    except Exception:
        await event.respond(f"Couldn't delete user.")


@client.on(events.NewMessage(pattern=r"/getinfo\s*(@?\w+)?"))
async def get_id(event, d=False):
    if not authorize(event): return

    try:
        par = event.pattern_match.group(1)

        if event.is_reply:
            msg = await event.get_reply_message()
            user = await msg.get_sender()
            id = user.id
        elif event.message.entities:
            for entity in event.message.entities:
                if isinstance(entity, MessageEntityMentionName):
                    id = entity.user_id
                    break
                elif par and "@" in par:
                    id = par
                elif par and par.isdigit():
                    id = int(par)
                else:
                    return

        user = await client.get_entity(id)
        if d:
            return user
        await event.reply(f"User: `{user.first_name} {user.last_name or ""}`\nID: `{user.id}`\nUsername: {f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"}\nPhone Number: {f"+{user.phone}" if user.phone else "Hiden"}\n"
                        f"Self: {user.is_self}\nPremium: {user.premium}\nVerified: {user.verified}\nRestricted: {user.restricted}  | Reason: {user.restriction_reason or "None"}\nStatus: {type(user.status).__name__}\nLanguage: {user.lang_code or "Not specified"}", parse_mode='md')
    except Exception as e:
        await event.reply("Couldn't find any user")
        log_error(f"{event.text}\n{e}")


@client.on(events.NewMessage(pattern='/enemies'))
async def list_enemies(event):
    if authorize(event):
        await event.respond(f"Enemies list:\n{'\n'.join(list(map(lambda usrid: f"- [{usrid}](tg://user?id={usrid})", user1.enemy)))}")


@client.on(events.NewMessage(pattern="/forcerep"))
async def force_reply(event):
    if not authorize(event): return
    
    if user1.replied:
        user1.replied = False
    else:
        user1.replied = True
    await event.reply(f"Force Reply {'Activated' if user1.replied else "Deactivated"}")


@client.on(events.NewMessage(pattern=r"/settime\s+(off|\d+-\d+)"))
async def set_time(event):
    if not authorize(event): return

    delay = event.pattern_match.group(1).split('-')
    if len(delay) == 2:
        user1.delay = list(map(int, delay))
        await event.reply(f"Delay set to {delay[0]}-{delay[1]}")
        return
    else:
        user1.delay = "off"
        await event.reply(f"Delay Deactivated")


@client.on(events.NewMessage(pattern=r"/spam (\d+)"))
async def spaming(event):
    if not authorize(event): return

    try:
        num = event.pattern_match.group(1)
        txt = await event.get_reply_message()
        txt = txt.text
        for _ in range(int(num)):
            async with client.action(event.chat_id, 'typing'):
                delay = user1.delay
                if delay != 'off':
                    asyncio.sleep(uniform(delay[0],delay[1]))
                await event.respond(txt)
    except Exception as e:
        await event.reply("Spam Failed.")
        log_error(f"{event.text}\n{e}")


@client.on(events.NewMessage(pattern="/reset"))
async def reset(event):
    if not authorize(event): return

    user1.boss = [boss_id]
    user1.enemy = []
    user1.said = []
    user1.delay = (2,7)
    user1.active = True
    user1.replied= True
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
        await event.reply("Running Already")


@client.on(events.NewMessage(pattern=r"/dcmd\s*(@?\w+)?"))
async def dcmd(event):
    if not authorize(event): return

    user = await get_id(event, d=True)
    if not user: return

    id = int(user.id)
    if int(event.sender_id) != boss_id: return await event.respond("Permission denied.")
    if id == boss_id: return await event.respond("Commander can't be dismissed")
    if id not in user1.boss: return await event.respond("User is not a commander")

    user1.boss.remove(id)
    await event.respond(f"Commander Deleted:\nName: {f"[{user.first_name}](tg://user?id={user.id})"}\nID: {user.id}")


@client.on(events.NewMessage(pattern=r"/cmds\s*(@?\w+)?"))
async def acmd(event):
    if not authorize(event): return
    await event.respond(f"Commanders list:\n{'\n'.join(list(map(lambda usrid: f"- [{usrid}](tg://user?id={usrid})", user1.boss)))}")


@client.on(events.NewMessage(pattern=r"/acmd\s*(@?\w+)?"))
async def acmd(event):
    if not authorize(event): return

    user = await get_id(event, d=True)
    if not user: return

    id = int(user.id)
    if int(event.sender_id) != boss_id: return await event.respond("Permission denied")
    if id in user1.enemy: return await event.respond("User is a enemy")
    if id in user1.boss: return await event.respond("User is already a commnader")

    user1.boss.append(id)
    await event.respond(f"New Commander added:\nName: {f"[{user.first_name}](tg://user?id={user.id})"}\nID: {user.id}")



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


@client.on(events.NewMessage(pattern=r"/cleanup\s+(https://t\.me/[^\s]+)\s*(\d+)?\s*(\d+)?"))
async def cleanup(event):
    if not authorize(event): return

    try:
        par = event.pattern_match
        link = par.group(1).strip()
        nums = int(par.group(2)) if par.group(2) else 2000
        st = abs(int(par.group(3))) if par.group(3) else 2

        report = await event.reply(f"Starting cleanup")
        try:
            msg = await parse_message_link(link)
            if not msg:
                raise Exception("Message Not Found")
            entity = await msg.get_chat()
        except Exception as e:
            await event.reply(f"Error resolving entity: {str(e)}")
            return

        total_deleted = delete_count = 0
        message_batch = []
        skipped = 0
        async for message in client.iter_messages(entity, limit=nums+st, from_user='me'):
            if skipped < st:
                skipped += 1
                continue

            message_batch.append(message.id)
            delete_count += 1
            if len(message_batch) >= randint(50, 90):
                try:
                    await client.delete_messages(entity, message_batch)
                    total_deleted += len(message_batch)
                    message_batch = []

                    delay = uniform(5,15)
                    await report.edit(f"Deleted {total_deleted}, Scanned {delete_count} messages so far. Waiting {delay:04.1f} secs...")
                    await asyncio.sleep(delay)

                except FloodWaitError as e:
                    wait = e.seconds + 5
                    await event.reply(f"⏳ Flood control: Waiting {wait} seconds")
                    await asyncio.sleep(wait)
        # Delete any remaining messages
        if message_batch:
            await client.delete_messages(entity, message_batch)
            total_deleted += len(message_batch)

        if total_deleted == 0:
            await report.edit(f"Flood control: Please wait a few minutes before trying again...")
        else:
            await report.edit(f"Clean up completed. Deleted {total_deleted} out of {delete_count} scanned.")

    except Exception as e:
        await event.reply(f"Cleanup Error: {str(e)}")
        log_error(f"{event.text}\n{e}")


@client.on(events.NewMessage(pattern="/help"))
async def help(event):
    if authorize(event):
        await event.respond("Commands:\n/add [ username | ID | reply | tag ] - Add an enemy.\n/del [ username | ID | reply | tag ] - Remove an enemy.\n/enemies - Show the list of all enemies.\n/spam [num] - Repeatedly repost the replied-to message a specified number of times.\n"
        "/forcerep - Toggle Reply Mode\n/settime [off | n-m] - Schedule a delay interval\n/sleep [time]:optional - Toggle Sleep Mode\n/run - Verify system status or Cancel Sleep Mode\n/kill - Shut Down the system permanently\n/reset - Reset all settings to default\n"
        "/save [ message link | reply ] - Archive a message\n/cvm -  Convert the replied message into a video note\n/rep [message link] [ message link | reply ]:optional - Reply to a message(first-parameter) with a message(second-parameter or reply)\n"
        "/getinfo [ username | ID | reply | tag ] - Retrieve user information.\n/acmd [ username | ID | reply | tag ]:optional - Add Commander role to a user or show the current Commander.\n/cleanup [group username] [limit]:optional [offset(use \" - \" from oldest)]:optional - Delete messages in a specific group.\nNote: Due to Telegram policy and the risk of Floodwait, the deletion limit is set to 2000 by default.\n"
        "/backup [chat ID]:optional - Back Up from all of the Chanels, Groups, Chats and Bots, or from specific chat messages, (Updating...)\n/help - Commands guide", parse_mode='md')


@client.on(events.NewMessage(pattern='/cvm'))
async def convert(event):
    if not authorize(event): return

    try:
        reply = await event.get_reply_message()
        async with client.action(event.chat_id, 'record-round'):
            input_path = await reply.download_media()
            output_path = convert_to_video_note(input_path)
        async with client.action(event.chat_id, 'round'):
            await client.send_file(event.chat_id, output_path, video_note=True)
    except:
        await event.reply(f"Unsupported video format, covert the file to .mp4(roecommended) format.")
    finally:
        clean_files(input_path, output_path)


@client.on(events.NewMessage(pattern=r"/rep\s+(https://t\.me/[^\s]+)(?:\s+(https://t\.me/[^\s]+))?"))
async def reply_with_message(event):
    if not authorize(event): return

    try:
        target_link = event.pattern_match.group(1)
        rep_msg = event.pattern_match.group(2)

        target_msg = await parse_message_link(target_link)

        if rep_msg:
            rep_msg = await parse_message_link(rep_msg)
        else:
            rep_msg = await event.get_reply_message()

        input_path = output_path = None
        if rep_msg.media:
            if rep_msg.video_note:
                async with client.action(target_msg.chat_id, 'record-round'):
                    input_path = await rep_msg.download_media()
                    output_path = convert_to_video_note(input_path)
                async with client.action(target_msg.chat_id, 'round'):
                    await client.send_file(target_msg.chat_id, output_path, reply_to=target_msg.id, video_note=True)
            else:
                async with client.action(target_msg.chat_id, f'{get_type(rep_msg)}'):
                    input_path = await rep_msg.download_media(f"{rep_msg.id}")
                    art = rep_msg.media.document.attributes if rep_msg.document else None
                    await client.send_file(target_msg.chat_id, input_path, caption=rep_msg.text or "", attributes=art, reply_to=target_msg.id, link_preview=False)
        else:
            async with client.action(target_msg.chat_id, 'typing'):
                await client.send_message(target_msg.chat_id, rep_msg.text, reply_to=target_msg.id, link_preview=False)

    except Exception as e:
        await event.reply(f"Reply Error: {e}")
        log_error(f"{event.text}\n{e}")
    finally:
        clean_files(input_path, output_path)


@client.on(events.NewMessage(pattern=r"/save\s*(@\w+|\d+|https://t\.me/[^\s]+)?(\s+(\d+))?"))
async def save_message(event):
    if not authorize(event): return

    try:
        async def saving(msg):
            user = msg.sender
            chat = await msg.get_chat()
            res = f"https://t.me/{msg.chat.username}/{msg.id}" if chat.username else f"https://t.me/c/{chat.id}/{msg.id}"

        # Export header
            if msg.is_private:
                header = f"User: {user.first_name} {user.last_name or " "}\nID: `{user.id}`\nUsername: {f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"}\nDate: {msg.date}\nReply to message ID: {msg.reply_to.reply_to_msg_id if msg.reply_to else 'None'}"
            elif chat.broadcast:
                header = f"Saved from {chat.title}\nChat ID: {chat.id}\nGenerated link: {res}\nCreation Date: {chat.date}\nBroadcast: {chat.broadcast}\n----------------------------"
            else:
                header = f"Saved from {chat.title}\nChat ID: {chat.id}\nGenerated link: {res}\n----------------------------\nUser: {user.first_name} {user.last_name or " "}\nID: {user.id}\nUsernmae: {f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})"}\nDate: {msg.date}\nReply to message ID: {msg.reply_to.reply_to_msg_id if msg.reply_to else 'None'}"

            input_path = output_path = None
            if msg.media:
                await event.reply("Downloading...")
                input_path = await msg.download_media(f"{msg.id}")
                print(1)
                if msg.video_note:
                    output_path = convert_to_video_note(input_path)
                    await client.send_file('me', output_path, video_note=True)
                else:
                    art = msg.media.document.attributes if msg.document else None
                    await client.send_file('me', input_path, caption=f"{header}\n\nCaption:\n{(msg.text or 'No Caption')}", attributes=art, link_preview=False)
            else:
                await client.send_message('me', f"{header}\n\nText:\n{msg.text}", link_preview=False)
            clean_files(input_path, output_path)

        link = event.pattern_match.group(1)
        if link and 'https' not in link:
            msg_list = await private(event)
            for msg in msg_list:
                await saving(msg)
        else:
            if link: 
                msg = await parse_message_link(link)
            else:
                msg = await event.get_reply_message()
            await saving(msg)

    except Exception as e:
        await event.reply(f"Saving Error: {str(e)}")
        log_error(f"{event.text}\n{e}")


def get_type(message):
    if not message.media:
        return "typing"

    if message.photo: return "photo"
    elif message.video: return "video"
    elif message.video_note: return "round"
    elif message.voice: return "record-voice"
    elif message.audio: return "audio"
    else: return "file"

async def private(event):
    print(1)
    user = event.pattern_match.group(1)
    if user.isdigit(): user = int(user)

    lim = event.pattern_match.group(2)
    lim = int(lim) if lim else 5

    messages = await client.get_messages(user, limit=lim)
    msg_list = [msg for msg in messages if msg.media]
    return msg_list

async def parse_message_link(link):
    try:        
        # Extract chat_id and message_id from URL
        parts = link.split('/')
        message_id = int(parts[-1]) 
        # Handle different URL formats
        chat_id = parts[-2]
        if parts[-2].isdigit():
            chat_id = int(parts[-2])

        entity = await client.get_entity(chat_id)

        return await client.get_messages(entity, ids=message_id)
    except Exception as e:
        log_error(f"Error parsing link {link}:\n{e}")
        return

def convert_to_video_note(input_path):
    try:
        fixed_path = f"fixed_{input_path}"

        clip = VideoFileClip(input_path)
        if clip.duration > 60:
            clip = clip.subclip(0, 60)
        width, height = clip.size
        size = min(width, height)
        croped = clip.cropped(x_center=width/2, y_center=height/2, width=size, height=size)
        resized = croped.resized(new_size=(640, 640))
        # Export
        resized.write_videofile(fixed_path, codec='libx264', audio_codec='aac', fps=30, threads=4)
        clip.close()
        resized.close()

        clean_files(input_path)
        fix_video_note(fixed_path, input_path) # over write
        return input_path  # output_path
    except Exception as e:
        log_error(f"Error Converting to video note:\n{e}")

def fix_video_note(input_path, output_path):
    try:
        cmd = ["ffmpeg", "-i", input_path, "-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart", "-preset", "fast", "-crf", "23", output_path]
        # Run FFmpeg
        subprocess.run(cmd, check=True)

        # Verify with MoviePy (optional)
        clip = VideoFileClip(output_path)
        clip.close()
    except Exception as e:
        log_error(f"Error ffmpeg:\n{e}")

def clean_files(*paths):
    for i in paths:
        try:
            os.remove(i)
        except:
            pass

# load sentences
def load_sens():
    lst = []
    with open(r"D:\u\prog\Python\attacker\sens.csv" , 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            lst.append(''.join(row))
    return lst

def log_error(error):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("errors.log", "a") as f:
        f.write(f"[{date}]\n{error}\n")
    logging.error(error)

# Randomly choose a sentence
def choose():
    if len(user1.sens) == 0: user1.sens = load_sens()
    w = user1.sens.pop(0)
    return w


async def sleep_timer(timer, event):
    try:
        await asyncio.sleep(timer)
        user1.active = True
        await event.reply("Sleep Mode ended")
    except asyncio.CancelledError:
        pass
    finally:
        user1.sleep_task = None

def authorize(event, opt=False):
    if opt:
        return event.sender_id in user1.boss
    return event.sender_id in user1.boss and user1.active



print("Connecting...")
client.start()
print("Logged in as user✔️")
client.run_until_disconnected()

