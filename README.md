# Telegram Tools Bot
Telegram CLI Bot is a powerful, feature-rich command-line interface for Telegram automation built with Python and Telethon. It provides enterprise-grade message management.

## Features
### Auto-Reply System
- Smart Response Engine: Automated replies to specified users with customizable delays
- Reply Mode Toggle: Switch between replying only to replies or every messages
- Configurable Delay: Set random delay intervals between responses or disable delays
- Sentence Rotation: Prevents message repetition with advanced cycling through response database

### User Management
- Enemy List System: Add/remove users to auto-reply list with multiple identification methods
- User Information: Comprehensive user data retrieval including ID, username, and status
- Authorization System: Secure command access restricted to authorized users

### Advanced Tools
- Message Cleanup: Bulk delete your messages from groups/chats with smart floodwait control
- Media Conversion: Convert videos to video notes (circular format)
- Cross-Chat Replies: Reply to messages in different chats using message links
- Message Archiving: Save any restricted messages with metadata to saved messages
- Spam Functionality: Repeated message sending with controlled delays
- Advanced link generation: Generate backup username if user does not have any username

### Bot Controls
- Sleep Mode: Temporary deactivation with optional timer
- System Reset: Restore all settings to defaults
- Commander Control: Transfer bot ownership to other users
- Graceful Shutdown: Complete bot termination
- Real-time Status: Monitor bot activity and settings

---

## Installation

#### Clone the repo:
```bash
git clone https://github.com/TAYMAZ328/telegram-cli-bot
cd telegram-cli-bot
```

#### Install dependencies:
```bash
pip install -r requirements.txt
```

#### Fill in Your Credentials:

Open the file named tocken.csv located in the project folder. Replace the placeholders with your actual Telegram API credentials:

```
tocken.csv

API_HASH ,API_ID, ADMIN_ID
```
- API_HASH: Get this from `my.telegram.org`
- API_ID: Also available from `my.telegram.org`
- ADMIN_ID: Your Telegram numeric user ID (not your username)

- Make sure the file contains a single line with comma-separated values and no extra spaces.


#### Run the application:
```bash
python script.py
```
