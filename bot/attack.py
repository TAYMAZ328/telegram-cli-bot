from telethon import events
from random import randint, uniform
import asyncio

from util import load_sens, authorize, log_error
from config import boss_id, user1
from script import client, get_id



@client.on(events.NewMessage())
async def handler(event):
    if not user1.active: return
    
    sender = int(event.sender_id)
    if sender in user1.boss or sender not in user1.enemy: return
    user1.last_msg[sender] = event # store last msg of the enemy for evil mode use
    
    try:
        if not user1.evil and eval("event.is_reply if user1.replied else True"):
            async with client.action(event.chat_id, 'typing'):
                delay = user1.delay
                if delay != 'off': await asyncio.sleep(uniform(delay[0],delay[1]))
                await event.reply(choose())
    except Exception as e:
        log_error(f"Error replying to enemy: {event.text}\n{e}")
        await event.respond("Failed to reply")


@client.on(events.NewMessage(pattern=r"/add\s*(?:(.+))?"))
async def add_enemy(event):
    if not authorize(event): return

    user = await get_id(event, d=True)
    try:
        if not user: return await event.reply("User ID couldn't be retrieved")
        id = int(user.id)
        if id in user1.enemy: return await event.reply("User is already added")
        if id in user1.boss: return await event.reply("User is admin")

        user1.enemy.append(id)
        await event.respond(f"Enemy [[{id}](tg://user?id={id})] added.")
    except Exception as e:
        log_error(f"Error adding enemy: {event.text}\n{e}")
        await event.reply(f"Couldn't add user")


@client.on(events.NewMessage(pattern=r"/del\s*(?:(.+))?"))
async def del_enemy(event):
    if not authorize(event): return
       
    user = await get_id(event, d=True)
    try:
        if not user: return await event.reply("User ID couldn't be retrieved")
        id = int(user.id)
        if id not in user1.enemy: return await event.reply("User does not exist in Enemy list")

        user1.enemy.remove(id)
        if id in user1.last_msg: del user1.last_msg[id]
        await event.respond(f"Enemy [[{id}](tg://user?id={id})] added.")

    except Exception as e:
        log_error(f"Error deleting enemy: {event.text}\n{e}")
        await event.reply(f"Couldn't delete user.")


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

    try:
        delay = event.pattern_match.group(1).split('-')
        if len(delay) == 2:
            user1.delay = list(map(int, delay))
            await event.reply(f"Delay set to {delay[0]}-{delay[1]}")
            return
        else:
            user1.delay = "off"
            await event.reply(f"Delay Deactivated")

    except Exception as e:
        log_error(f"Error settime: {event.text}\n{e}")
        await event.reply("Failed to set time")


@client.on(events.NewMessage(pattern=r"/setlevel\s*(off|1|2|3)?"))
async def senlevel(event):
    if not authorize(event): return

    try:
        lvl = event.pattern_match.group(1)
        if not lvl: return await event.reply(f"Level is set to [ {user1.lvl[2]} ]")
        
        if lvl == "off":
            user1.lvl = [None, None, "off"]
        elif lvl == "1":
            user1.lvl = [None, 60, "1"]
        elif lvl == "2":
            user1.lvl = [60, 130, "2"]
        elif lvl == "3":
            user1.lvl = [130, None, "3"]

        user1.sens.clear()
        await event.reply(f"Level set to {lvl}")

    except Exception as e:
        log_error(f"Error setlevel: {event.text}\n{e}")
        await event.reply("Failed to set level")


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
        log_error(f"Error spamming: {event.text}\n{e}")
        await event.reply("Spaming Failed")


@client.on(events.NewMessage(pattern="/evilmode"))
async def evil_mode(event):
    if not authorize(event): return
    
    if user1.evil:
        user1.evil = False
        await event.respond("Evil mode Deactivated")
        return
    user1.evil = True
    await event.respond("Evil mode Activated")

    try:
        async with client.action(event.chat_id, 'typing'):
            while user1.evil and user1.enemy:
                for enemy in user1.enemy:
                    msg = user1.last_msg.get(enemy, None)
                    if not user1.last_msg:
                        await event.respond("Last message couldn't be retrieved")
                        if user1.evil: await evil_mode(event)
                        return
                    if not msg: break
                    delay = user1.delay
                    if delay != 'off': await asyncio.sleep(uniform(delay[0],delay[1]))
                    await msg.reply(choose())
            else:
                if not user1.enemy: await event.reply("No enemy")

        if user1.evil: await evil_mode(event)

    except Exception as e:
        log_error(f"Evil mode operation failure: {event.text}\n{e}")
        await event.reply("Evil mode Failed")
        user1.evil = False


@client.on(events.NewMessage(pattern=r"/dcmd\s*(@?\w+)?"))
async def dcmd(event):
    if not authorize(event): return

    user = await get_id(event, d=True)

    try:
        if not user: return
        id = int(user.id)
        if int(event.sender_id) != boss_id: return await event.reply("Permission denied")
        if id == boss_id: return await event.reply("Commander can't be dismissed")
        if id not in user1.boss: return await event.reply("User is not a commander")

        user1.boss.remove(id)
        await event.respond(f"Commander Deleted:\nName: {f"[{user.first_name}](tg://user?id={user.id})"}\nID: {user.id}")

    except Exception as e:
        log_error(f"Error deleting commander: {event.text}\n{e}")
        await event.reply("Couldn't delete commander")


@client.on(events.NewMessage(pattern=r"/cmds\s*(@?\w+)?"))
async def cmds(event):
    if not authorize(event): return
    await event.respond(f"Commanders list:\n{'\n'.join(list(map(lambda usrid: f"- [{usrid}](tg://user?id={usrid})", user1.boss)))}")


@client.on(events.NewMessage(pattern=r"/acmd\s*(@?\w+)?"))
async def acmd(event):
    if not authorize(event): return

    user = await get_id(event, d=True)

    try:
        if not user: return
        id = int(user.id)
        if int(event.sender_id) != boss_id: return await event.reply("Permission denied")
        if id in user1.enemy: return await event.reply("User is a enemy")
        if id in user1.boss: return await event.reply("User is already a commnader")

        user1.boss.append(id)
        await event.respond(f"New Commander added:\nName: {f"[{user.first_name}](tg://user?id={user.id})"}\nID: {user.id}")

    except Exception as e:
        log_error(f"Error adding commander: {event.text}\n{e}")
        await event.reply("Couldn't add commander")


# Randomly choose a sentence
def choose():
    if len(user1.sens) == 0: user1.sens = load_sens()
    w = user1.sens.pop(randint(0, len(user1.sens)-1))
    return w