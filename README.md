# How to Create Discord Bots
A full guide on how to make a basic Discord bot by The Abyss Team

I've been a discord.py dev for a long time (since 2021), and I know the frustration of creating these applications and how hard it is for beginners. So I made this documentation in Python for those people

# 1. Requirements
- Have a Discord account (if you have any questions, ask me on Discord: "immilkk")
- One Discord server with you as an administrator
- Python 3.10+
- Basic knowledge about Discord, like functions, classes, and simple logic

# 2. Creating the Discord bot in Discord
Discord allows you to create bots in the [Discord Developer Portal](https://discord.com/developers/applications)
- In applications, click on "New Application"
- Create a cool name for the bot, like "The Abyss"
- Go to the Bot tab and click on "Add Bot"
- Copy the Token
**WARNING: DO NOT SHARE THE DISCORD BOT TOKEN!!!**

# 3. Invite the bot to the server
The bot only works if you add it to the server
- Go to OAuth2/URL Generator
- Go to the Scopes tab and select:
  - Bot
  - applications.commands
- In Bot Permissions, choose the basic permissions:
    - Send Messages
    - Read Message History
  - Copy and paste in browser
  - Choose the server

# 4. Creating the Files
Before starting, it's necessary to have a Virtual Environment. For this, run the command:
```bash
python -m venv .venv
```
Now, activate the venv with the command:
```powershell
.\.venv\Scripts\activate
```
```bash
source venv/bin/activate
```
Download discord.py:
```bash
pip install -U discord.py
```

# 5. Minimal code for the bot
I'm going to show all the code for better comprehension:
```python
import discord # Import the discord lib
from discord.ext import commands

intents = discord.Intents.default() # The discord bot intents can be found in bot tab
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents) # Declare the bot command

@bot.event # Event in discord bot
async def on_ready():
  print(f"Bot connected as {bot.user}")

@bot.command() # Create a command
async def ping(ctx): # Command entry point
  await ctx.send("Pong!") # Response

bot.run("YOUR_TOKEN") # API Key
```

# 6. Basic Concepts
- Intents: permissions that tell the bot what it can allow or deny on Discord
- Events: automatic actions (ex: on_ready, on_message)
- Commands: activate commands by prefix or slash
- ctx (context): information about who used the command

# 7. Next Steps
- Slash Commands
- Cogs
- Database (SQLite3 or PostgreSQL)
- Hosting (Railway, VPS, Docker)
- Role permission systems

# 8. Good Tips
- NEVER commit the Discord token to GitHub
- Use Environment Variables
- Organize commands into separate files
- Use try/except for error handling
