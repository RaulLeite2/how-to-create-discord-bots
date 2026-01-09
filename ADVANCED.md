# Advanced Discord Bot Development
Advanced concepts and implementations for Discord bots using discord.py

This guide assumes you've completed the basic tutorial and have a working Discord bot.

---

## Table of Contents
1. [Cogs - Organizing Your Bot](#1-cogs---organizing-your-bot)
2. [Slash Commands](#2-slash-commands)
3. [Command Groups](#3-command-groups)
4. [Database Integration](#4-database-integration)

---

## 1. Cogs - Organizing Your Bot

Cogs are modules that help organize your bot's commands and events into separate files, making your code cleaner and more maintainable.

### Project Structure
```
bot/
├── main.py
├── cogs/
│   ├── __init__.py
│   ├── moderation.py
│   └── fun.py
└── .env
```

### Creating a Cog

**cogs/moderation.py**
```python
import discord
from discord.ext import commands

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Moderation cog loaded")
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason=None):
        """Kicks a member from the server"""
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} has been kicked. Reason: {reason}")
    
    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason=None):
        """Bans a member from the server"""
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} has been banned. Reason: {reason}")

# Required function to load the cog
async def setup(bot):
    await bot.add_cog(Moderation(bot))
```

**cogs/fun.py**
```python
import discord
from discord.ext import commands
import random

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="roll")
    async def roll_dice(self, ctx, dice: str = "1d6"):
        """Rolls dice in NdN format (e.g., 2d6)"""
        try:
            rolls, sides = map(int, dice.split('d'))
            results = [random.randint(1, sides) for _ in range(rolls)]
            await ctx.send(f"🎲 Results: {results}\nTotal: {sum(results)}")
        except Exception:
            await ctx.send("Format must be NdN (e.g., 2d6)")
    
    @commands.command(name="8ball")
    async def magic_8ball(self, ctx, *, question: str):
        """Ask the magic 8-ball a question"""
        responses = [
            "Yes, definitely", "It is certain", "Without a doubt",
            "Ask again later", "Cannot predict now", "Concentrate and ask again",
            "Don't count on it", "My reply is no", "Outlook not so good"
        ]
        await ctx.send(f"🎱 {random.choice(responses)}")

async def setup(bot):
    await bot.add_cog(Fun(bot))
```

### Loading Cogs in main.py

```python
import discord
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")
    print(f"Loaded {len(bot.cogs)} cogs")

async def load_cogs():
    """Load all cogs from the cogs folder"""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'cogs.{filename[:-3]}')
            print(f"Loaded cog: {filename}")

async def main():
    async with bot:
        await load_cogs()
        await bot.start("YOUR_TOKEN")

if __name__ == "__main__":
    asyncio.run(main())
```

### Cog Management Commands

```python
# Reload a cog (useful for development)
@bot.command()
@commands.is_owner()
async def reload(ctx, extension):
    await bot.reload_extension(f'cogs.{extension}')
    await ctx.send(f"✅ Reloaded {extension}")

# Unload a cog
@bot.command()
@commands.is_owner()
async def unload(ctx, extension):
    await bot.unload_extension(f'cogs.{extension}')
    await ctx.send(f"✅ Unloaded {extension}")
```

---

## 2. Slash Commands

Slash commands are modern Discord commands that appear in the Discord UI with auto-complete and parameter validation.

### Basic Slash Command Setup

```python
import discord
from discord import app_commands
from discord.ext import commands

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Sync commands with Discord
    await bot.tree.sync()
    print(f"Bot ready! Synced {len(bot.tree.get_commands())} commands")

@bot.tree.command(name="hello", description="Say hello to the bot")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hello {interaction.user.mention}! 👋")

@bot.tree.command(name="userinfo", description="Get information about a user")
@app_commands.describe(user="The user to get info about")
async def userinfo(interaction: discord.Interaction, user: discord.Member = None):
    user = user or interaction.user
    
    embed = discord.Embed(title=f"User Info: {user.name}", color=user.color)
    embed.add_field(name="ID", value=user.id)
    embed.add_field(name="Joined Server", value=user.joined_at.strftime("%Y-%m-%d"))
    embed.add_field(name="Account Created", value=user.created_at.strftime("%Y-%m-%d"))
    embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
    
    await interaction.response.send_message(embed=embed)

bot.run("YOUR_TOKEN")
```

### Slash Commands with Choices

```python
@bot.tree.command(name="color", description="Choose your favorite color")
@app_commands.describe(color="Pick a color")
@app_commands.choices(color=[
    app_commands.Choice(name="Red", value="red"),
    app_commands.Choice(name="Blue", value="blue"),
    app_commands.Choice(name="Green", value="green"),
    app_commands.Choice(name="Yellow", value="yellow")
])
async def favorite_color(interaction: discord.Interaction, color: app_commands.Choice[str]):
    await interaction.response.send_message(f"You chose {color.name}! 🎨")
```

### Slash Commands in Cogs

```python
from discord import app_commands
from discord.ext import commands

class SlashCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="ping", description="Check bot latency")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong! Latency: {latency}ms")
    
    @app_commands.command(name="serverinfo", description="Get server information")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild
        
        embed = discord.Embed(title=f"{guild.name} Info", color=discord.Color.blue())
        embed.add_field(name="Members", value=guild.member_count)
        embed.add_field(name="Owner", value=guild.owner.mention)
        embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"))
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(SlashCog(bot))
```

---

## 3. Command Groups

Command groups organize related commands under a parent command.

### Traditional Command Groups

```python
@bot.group(name="config", invoke_without_command=True)
@commands.has_permissions(administrator=True)
async def config(ctx):
    """Configuration commands"""
    await ctx.send("Available subcommands: prefix, welcomechannel")

@config.command(name="prefix")
async def config_prefix(ctx, new_prefix: str):
    """Change the bot prefix"""
    # Save to database (see database section)
    await ctx.send(f"✅ Prefix changed to: {new_prefix}")

@config.command(name="welcomechannel")
async def config_welcome(ctx, channel: discord.TextChannel):
    """Set the welcome channel"""
    # Save to database
    await ctx.send(f"✅ Welcome channel set to: {channel.mention}")
```

### Slash Command Groups

```python
class ModerationGroup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    # Create a command group
    mod_group = app_commands.Group(name="mod", description="Moderation commands")
    
    @mod_group.command(name="timeout", description="Timeout a member")
    @app_commands.describe(member="The member to timeout", duration="Duration in minutes")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int):
        """Timeout a member"""
        from datetime import timedelta
        
        await member.timeout(timedelta(minutes=duration))
        await interaction.response.send_message(f"⏱️ {member.mention} has been timed out for {duration} minutes")
    
    @mod_group.command(name="untimeout", description="Remove timeout from a member")
    @app_commands.describe(member="The member to remove timeout from")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def untimeout(self, interaction: discord.Interaction, member: discord.Member):
        """Remove timeout from a member"""
        await member.timeout(None)
        await interaction.response.send_message(f"✅ Timeout removed from {member.mention}")
    
    @mod_group.command(name="warn", description="Warn a member")
    @app_commands.describe(member="The member to warn", reason="Reason for warning")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        """Warn a member"""
        # Save warning to database
        await interaction.response.send_message(f"⚠️ {member.mention} has been warned for: {reason}")

async def setup(bot):
    await bot.add_cog(ModerationGroup(bot))
```

---

## 4. Database Integration

### Using SQLite3 (Built-in Python)

**database.py**
```python
import sqlite3
import aiosqlite
from typing import Optional

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
    
    async def setup(self):
        """Initialize database tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # User data table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    coins INTEGER DEFAULT 0
                )
            """)
            
            # Server configuration table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_config (
                    guild_id INTEGER PRIMARY KEY,
                    prefix TEXT DEFAULT '!',
                    welcome_channel INTEGER,
                    log_channel INTEGER
                )
            """)
            
            # Warnings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    moderator_id INTEGER,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.commit()
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user data"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def create_user(self, user_id: int, username: str):
        """Create a new user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
                (user_id, username)
            )
            await db.commit()
    
    async def add_xp(self, user_id: int, xp: int):
        """Add XP to a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET xp = xp + ? WHERE user_id = ?",
                (xp, user_id)
            )
            await db.commit()
    
    async def add_warning(self, user_id: int, guild_id: int, moderator_id: int, reason: str):
        """Add a warning to a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO warnings (user_id, guild_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
                (user_id, guild_id, moderator_id, reason)
            )
            await db.commit()
    
    async def get_warnings(self, user_id: int, guild_id: int) -> list:
        """Get all warnings for a user in a guild"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM warnings WHERE user_id = ? AND guild_id = ? ORDER BY timestamp DESC",
                (user_id, guild_id)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
```

**Installing aiosqlite:**
```bash
pip install aiosqlite
```

### Using the Database in Your Bot

**main.py**
```python
import discord
from discord.ext import commands
from database import Database

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
bot.db = Database()

@bot.event
async def on_ready():
    await bot.db.setup()
    print(f"Bot ready! Database initialized.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    # Add XP for each message
    await bot.db.create_user(message.author.id, str(message.author))
    await bot.db.add_xp(message.author.id, 5)
    
    await bot.process_commands(message)

@bot.command(name="profile")
async def profile(ctx, member: discord.Member = None):
    """View user profile"""
    member = member or ctx.author
    
    user_data = await bot.db.get_user(member.id)
    if not user_data:
        await ctx.send("User not found in database!")
        return
    
    embed = discord.Embed(title=f"{member.name}'s Profile", color=member.color)
    embed.add_field(name="Level", value=user_data['level'])
    embed.add_field(name="XP", value=user_data['xp'])
    embed.add_field(name="Coins", value=user_data['coins'])
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    
    await ctx.send(embed=embed)

bot.run("YOUR_TOKEN")
```

### Using PostgreSQL (Production-Ready)

**Installing asyncpg:**
```bash
pip install asyncpg
```

**postgres_database.py**
```python
import asyncpg
from typing import Optional

class PostgresDatabase:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Create connection pool"""
        self.pool = await asyncpg.create_pool(self.dsn)
    
    async def setup(self):
        """Initialize database tables"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    xp INTEGER DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    coins INTEGER DEFAULT 0
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS warnings (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT,
                    guild_id BIGINT,
                    moderator_id BIGINT,
                    reason TEXT,
                    timestamp TIMESTAMP DEFAULT NOW()
                )
            """)
    
    async def get_user(self, user_id: int) -> Optional[dict]:
        """Get user data"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
            return dict(row) if row else None
    
    async def close(self):
        """Close connection pool"""
        await self.pool.close()
```

---

## Best Practices

### 1. Environment Variables
Never hardcode tokens. Use a `.env` file:

**.env**
```
DISCORD_TOKEN=your_token_here
DATABASE_URL=postgresql://user:password@localhost/dbname
```

**Install python-dotenv:**
```bash
pip install python-dotenv
```

**Load environment variables:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
```

### 2. Error Handling

```python
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: {error.param.name}")
    elif isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    else:
        print(f"Error: {error}")
```

### 3. Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('discord')
```

---

## Next Steps

- Implement pagination for long lists
- Add reaction roles
- Create economy system with transactions
- Implement music player
- Add custom embeds builder
- Create dashboard with web interface
- Implement rate limiting and cooldowns

---

## Useful Resources

- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Portal](https://discord.com/developers/docs)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
