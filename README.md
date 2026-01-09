# How to Create Discord Bots
A full guide how to make a basic discord bot by The Abyss Team

I'm a dev from discord.py for a long time(since 2021), and i know the frustation about creating this aplications and how hard for initiante people. So a make this documentation in Python for those people

# 1. Requirements
- Have a discord account(if you have any question, ask me in discord "immilkk")
- One Discord server with you as an administrator permission
- Python 3.10+
- Basic Knowledge about discord, like, funcitons, class, and simple logic

# 2. Creating the discord bot in Discord
The discord allow you to create in [Discord Develper Portal](https://discord.com/developers/applications)
- In applications, click in "New Aplication"
- Create a cool name for the bot, like "The Abyss"
- Go to the Bot tab and click in add bot
- Copy the Toker
**WARNING: DO NOT SHARE THE DISCORD BOT TOKEN!!!**

# 3. Invite the bot for the server
The Bot only work if you add them to the server
- Got to OAuth2/URL Generator
- Got to Scopes tab and select:
  - Bot
  - applications.commands
- In Bot Permissions, chose the basic permissions:
    - Send Messages
    - Read Message History
  - Copy and paste in browser
  - Chose the server

# 4. Creating the Files
Before starting, its necessary you have the Virtual Envoriment, for this, run the command:
```
python -m venv .venv
```
Now, activate the venv with command:
```windows
.\.venv\Scripts\activate
```
``` Linux/Mac
source venv/bin/activate
```
Download discord.py
``` Linux/Mac
pip install -U discord.py
```

# 5. Minimal code from bot
I'm going to commit all the code for more compreense:
```python
import discord # Import the discord lib
from discord.ext import commands

intents = discord.Intents.default() # The discord bot intents can be found in bot tab
intents.message_conent = True

bot = commands.Bot(command_prefix="!", intents=intents) # Declare the bot command

@bot.event # Event in discord bot
async def on_ready():
  print("Bot connected with {bot.user}")

@bot.command() # Create a command
async def ping(ctx): # Enter of command
  await ctx.send("Pong!") # Reponse

bot.run("YOUR_TOKEN") # API Key
```

# 6. Basic Concepts
- Intents: permissions that says to bot what he can allow or deny on discord
- Events: automatic actions(ex: on_ready, on_message)
- commands: activate commands by prefix or slash
- ctx(context): informatios about who use the command

# 7. Next Steps
- Slash Commands
- Cogs
- Database(SQLite3 or PostgreSQL)
- Host(Railway, VPS, Docker)
- System of role perms

# 8. Good Tips
- NEVER commit the discord token on GitHub
- Use Ambient Variables
- Spread the command with files
- use try/execpt for errors
