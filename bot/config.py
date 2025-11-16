from dotenv import load_dotenv
import os
load_dotenv()

boss_id = int(os.getenv("ADMIN_ID"))

class UserConfig:
    boss = [boss_id]
    enemy = []
    sens = []
    delay = (2,7)
    active = True
    replied= True
    evil = False
    lvl = [None, None, "off"]
    last_msg = {}
    sleep_task = None
user1 = UserConfig()