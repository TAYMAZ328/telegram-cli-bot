import asyncio, csv, os, logging
from datetime import datetime
from config import user1


async def parse_message_link(link):
    from script import client
    try:        
        # Extract chat_id and message_id from URL
        parts = link.split('/')
        message_id = int(parts[-1]) 
        # Handle different URL formats
        chat_id = parts[-2]
        if parts[-2].isdigit(): chat_id = int(parts[-2])

        entity = await client.get_entity(chat_id)

        return await client.get_messages(entity, ids=message_id)
    except Exception as e:
        log_error(f"Error parsing link: {link}\n{e}")
        return
    

def get_type(message):
    if not message.media:
        return "typing"

    if message.photo: return "photo"
    elif message.video: return "video"
    elif message.video_note: return "round"
    elif message.voice: return "record-voice"
    elif message.audio: return "audio"
    else: return "file"


def clean_files(*paths):
    for i in paths:
        try:
            os.remove(i)
        except:
            pass

# load sentences
def load_sens():
    lst = []
    with open(os.path.join("files", "users.csv") , 'r', encoding='utf-8') as f:
        for row in csv.reader(f):
            lst.append(''.join(row))
    return lst[user1.lvl[0] : user1.lvl[1]]

def log_error(error):
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join("files", "errors.log"), "a") as f:
        f.write(f"[{date}]\n{error}\n")
    logging.error(error)


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

