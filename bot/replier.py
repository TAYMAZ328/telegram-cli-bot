from telethon import events

from util import authorize, parse_message_link, get_type, log_error, clean_files
from cvm import convert_to_video_note
from script import client


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
        await event.reply("Failed to reply")
        log_error(f"Error reply: {event.text}\n{e}")
    finally:
        clean_files(input_path, output_path)