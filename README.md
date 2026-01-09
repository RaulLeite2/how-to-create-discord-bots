# How to Create Discord Bots with Python

A comprehensive guide on creating Discord bots using Python and the Discord API by The Abyss Team.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Step 1: Setting Up Your Discord Application](#step-1-setting-up-your-discord-application)
- [Step 2: Installing Required Libraries](#step-2-installing-required-libraries)
- [Step 3: Creating Your Bot](#step-3-creating-your-bot)
- [Step 4: Running Your Bot](#step-4-running-your-bot)
- [Step 5: Adding Commands](#step-5-adding-commands)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Resources](#resources)

## Prerequisites

Before you begin, make sure you have the following:

- Python 3.8 or higher installed on your system
- A Discord account
- Basic knowledge of Python programming
- A text editor or IDE (VS Code, PyCharm, etc.)

## Step 1: Setting Up Your Discord Application

### 1.1 Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click on "New Application" button
3. Give your application a name (this will be your bot's name)
4. Click "Create"

### 1.2 Create a Bot User

1. In your application page, navigate to the "Bot" section in the left sidebar
2. Click "Add Bot"
3. Click "Yes, do it!" to confirm
4. Your bot is now created! You'll see a TOKEN section - this is your bot's token

⚠️ **Important:** Never share your bot token publicly! Anyone with your token can control your bot.

### 1.3 Configure Bot Permissions

1. In the "Bot" section, scroll down to "Privileged Gateway Intents"
2. Enable the following intents based on your needs:
   - **Presence Intent** - if your bot needs to see user status
   - **Server Members Intent** - if your bot needs to access member information
   - **Message Content Intent** - if your bot needs to read message content

### 1.4 Invite Your Bot to a Server

1. Go to the "OAuth2" section, then "URL Generator"
2. Under "Scopes", select `bot`
3. Under "Bot Permissions", select the permissions your bot needs:
   - For a basic bot: `Send Messages`, `Read Messages/View Channels`
   - For more advanced features, add permissions as needed
4. Copy the generated URL at the bottom
5. Open the URL in your browser and select a server to add your bot to

## Step 2: Installing Required Libraries

### 2.1 Create a Virtual Environment (Recommended)

```bash
# Create a virtual environment
python -m venv bot-env

# Activate it
# On Windows:
bot-env\Scripts\activate
# On macOS/Linux:
source bot-env/bin/activate
```

### 2.2 Install discord.py

```bash
pip install discord.py
```

For additional features, you can install:

```bash
# Install with voice support
pip install discord.py[voice]

# Install python-dotenv for environment variables
pip install python-dotenv
```

## Step 3: Creating Your Bot

### 3.1 Set Up Your Project Structure

Create a new directory for your bot project:

```
my-discord-bot/
├── bot.py
├── .env
└── .env.example
```

### 3.2 Create Environment Variables File

Create a `.env` file to store your bot token securely:

```
DISCORD_TOKEN=your_bot_token_here
```

Create a `.env.example` file (to share the structure without exposing your token):

```
DISCORD_TOKEN=your_bot_token_here
```

### 3.3 Write Your Bot Code

Create `bot.py` with a basic bot structure:

```python
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Create bot instance with intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    if message.content == 'hello':
        await message.channel.send('Hello! 👋')
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='ping')
async def ping(ctx):
    """Responds with 'Pong!'"""
    await ctx.send('Pong!')

@bot.command(name='info')
async def info(ctx):
    """Displays bot information"""
    embed = discord.Embed(
        title="Bot Information",
        description="A simple Discord bot created with discord.py",
        color=discord.Color.blue()
    )
    embed.add_field(name="Servers", value=len(bot.guilds), inline=True)
    embed.add_field(name="Latency", value=f"{round(bot.latency * 1000)}ms", inline=True)
    await ctx.send(embed=embed)

# Run the bot
bot.run(TOKEN)
```

## Step 4: Running Your Bot

1. Make sure your `.env` file contains your bot token
2. Activate your virtual environment (if you created one)
3. Run the bot:

```bash
python bot.py
```

You should see output similar to:
```
YourBotName#1234 has connected to Discord!
Bot is in 1 guilds
```

4. Test your bot in Discord by typing:
   - `hello` - The bot should respond with "Hello! 👋"
   - `!ping` - The bot should respond with "Pong!"
   - `!info` - The bot should display information about itself

## Step 5: Adding Commands

### 5.1 Simple Command

```python
@bot.command(name='greet')
async def greet(ctx, name):
    """Greets a user by name"""
    await ctx.send(f'Hello, {name}! 👋')
```

Usage: `!greet John` → "Hello, John! 👋"

### 5.2 Command with Multiple Arguments

```python
@bot.command(name='add')
async def add(ctx, num1: int, num2: int):
    """Adds two numbers"""
    result = num1 + num2
    await ctx.send(f'{num1} + {num2} = {result}')
```

Usage: `!add 5 3` → "5 + 3 = 8"

### 5.3 Command with Error Handling

```python
@bot.command(name='divide')
async def divide(ctx, num1: float, num2: float):
    """Divides two numbers"""
    if num2 == 0:
        await ctx.send('Error: Cannot divide by zero!')
        return
    result = num1 / num2
    await ctx.send(f'{num1} ÷ {num2} = {result:.2f}')

@divide.error
async def divide_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please provide two numbers: !divide <num1> <num2>')
    elif isinstance(error, commands.BadArgument):
        await ctx.send('Please provide valid numbers!')
```

### 5.4 Command with Embeds

```python
@bot.command(name='serverinfo')
async def serverinfo(ctx):
    """Displays server information"""
    if not ctx.guild:
        await ctx.send("This command can only be used in a server!")
        return
    
    guild = ctx.guild
    embed = discord.Embed(
        title=f"{guild.name}",
        description=f"Server information for {guild.name}",
        color=discord.Color.green()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    owner_mention = guild.owner.mention if guild.owner else "Unknown"
    embed.add_field(name="Owner", value=owner_mention, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    await ctx.send(embed=embed)
```

## Best Practices

### Security

1. **Never hardcode your token** - Always use environment variables
2. **Add `.env` to `.gitignore`** - Prevent accidentally committing your token
3. **Regenerate your token** if it's ever exposed
4. **Use role-based permissions** - Restrict certain commands to specific roles

### Code Organization

1. **Use cogs** for organizing commands into categories:

```python
# cogs/moderation.py
import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f'{member.mention} has been kicked.')

async def setup(bot):
    await bot.add_cog(Moderation(bot))
```

2. **Add error handling** for all commands
3. **Use meaningful command names and descriptions**
4. **Add logging** to track bot activity

### Performance

1. **Use intents wisely** - Only enable intents you need
2. **Implement rate limiting** for command-heavy bots
3. **Use async/await properly** - Don't block the event loop
4. **Cache data** when appropriate to reduce API calls

### User Experience

1. **Provide helpful error messages**
2. **Use embeds** for better formatting
3. **Add command cooldowns** to prevent spam
4. **Include a help command** (discord.py provides one by default)

## Troubleshooting

### Common Issues

**Bot doesn't respond to commands:**
- Make sure `message_content` intent is enabled in the Developer Portal
- Verify that `intents.message_content = True` is in your code
- Check that you're calling `await bot.process_commands(message)` in `on_message`

**Bot can't connect:**
- Verify your token is correct
- Check your internet connection
- Ensure the token isn't accidentally wrapped in quotes in the `.env` file

**Permission errors:**
- Check bot permissions in the Discord server
- Verify the bot has the required permissions for the action
- Make sure the bot's role is high enough in the role hierarchy

**ModuleNotFoundError: No module named 'discord':**
- Make sure you've installed discord.py: `pip install discord.py`
- Verify you're using the correct Python environment

### Getting Help

- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [discord.py Discord Server](https://discord.gg/dpy)
- [Discord Developer Documentation](https://discord.com/developers/docs/)

## Resources

### Official Documentation
- [Discord.py Documentation](https://discordpy.readthedocs.io/en/stable/)
- [Discord API Documentation](https://discord.com/developers/docs/intro)
- [Discord Developer Portal](https://discord.com/developers/applications)

### Tutorials and Guides
- [discord.py GitHub Repository](https://github.com/Rapptz/discord.py)
- [Discord.py Examples](https://github.com/Rapptz/discord.py/tree/master/examples)

### Community
- [Discord.py Discord Server](https://discord.gg/dpy)
- [r/Discord_Bots Subreddit](https://www.reddit.com/r/Discord_Bots/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ by The Abyss Team
