from telethon import events
from telethon.errors import FloodWaitError
from random import randint, uniform
import asyncio

from script import client
from util import parse_message_link, authorize, log_error


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