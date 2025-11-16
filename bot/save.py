from telethon import events

from script import client
from util import authorize, parse_message_link, log_error, clean_files
from cvm import convert_to_video_note

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


async def private(event):
    user = event.pattern_match.group(1)
    if user.isdigit(): user = int(user)

    lim = event.pattern_match.group(2)
    lim = int(lim) if lim else 5

    messages = await client.get_messages(user, limit=lim)
    msg_list = [msg for msg in messages if msg.media]
    return msg_list