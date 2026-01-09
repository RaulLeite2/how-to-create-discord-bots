# Code Style Guide
**Mandatory standards for Discord bot development**

This document defines code standards, naming conventions, and organization rules. Following these guidelines prevents technical debt and ensures maintainability.

---

## Table of Contents
1. [Python Standards](#python-standards)
2. [Naming Conventions](#naming-conventions)
3. [File Organization](#file-organization)
4. [Code Structure](#code-structure)
5. [Documentation](#documentation)
6. [What is Forbidden](#what-is-forbidden)
7. [What is Mandatory](#what-is-mandatory)
8. [Error Handling](#error-handling)
9. [Database Practices](#database-practices)
10. [Discord-Specific Rules](#discord-specific-rules)

---

## Python Standards

### PEP 8 Compliance
Follow [PEP 8](https://pep8.org/) for all Python code.

**Key points:**
- Use 4 spaces for indentation (never tabs)
- Maximum line length: 88 characters (Black default)
- Two blank lines between top-level functions/classes
- One blank line between methods in a class

### Formatting Tools
**MANDATORY:** Use these tools before committing:

```bash
# Install formatting tools
pip install black isort flake8 mypy

# Format code
black .

# Sort imports
isort .

# Check for issues
flake8 .

# Type checking
mypy .
```

### Python Version
- **Minimum:** Python 3.10+
- **Recommended:** Python 3.11+
- Use modern syntax (type hints, match statements, etc.)

---

## Naming Conventions

### Variables and Functions
```python
# Snake case for variables and functions
user_count = 0
message_content = ""

async def send_welcome_message():
    pass

async def calculate_user_level(xp: int) -> int:
    pass
```

### Classes
```python
# PascalCase for classes
class ModerationCog(commands.Cog):
    pass

class DatabaseManager:
    pass

class UserProfile:
    pass
```

### Constants
```python
# UPPER_SNAKE_CASE for constants
MAX_MESSAGE_LENGTH = 2000
DEFAULT_PREFIX = "!"
EMBED_COLOR = 0x5865F2
COOLDOWN_SECONDS = 60
```

### Private Methods
```python
class BotManager:
    def __init__(self):
        self._internal_state = {}  # Private attribute
    
    def _process_data(self):  # Private method
        pass
    
    def public_method(self):  # Public method
        pass
```

### Cog Names
```python
# Cogs should be descriptive and end with "Cog"
class ModerationCog(commands.Cog):
    pass

class EconomyCog(commands.Cog):
    pass

class FunCommandsCog(commands.Cog):
    pass
```

### Command Names
```python
# Command names: lowercase, underscores for multi-word
@bot.command(name="kick")
async def kick_command(ctx):
    pass

@bot.command(name="user_info")
async def user_info_command(ctx):
    pass

# Slash commands: lowercase, no underscores (Discord limitation)
@bot.tree.command(name="userinfo")
async def userinfo_slash(interaction):
    pass
```

### File Names
```
# Snake case for Python files
moderation_cog.py
database_manager.py
user_utils.py
config_loader.py

# Special files
main.py
config.py
__init__.py
```

---

## File Organization

### Project Structure
```
bot/
├── main.py                 # Entry point
├── config.py              # Configuration management
├── requirements.txt       # Dependencies
├── .env.example          # Example environment variables
├── .gitignore            # Git ignore rules
│
├── cogs/                 # Command modules
│   ├── __init__.py
│   ├── moderation.py
│   ├── economy.py
│   ├── fun.py
│   └── admin.py
│
├── utils/                # Utility functions
│   ├── __init__.py
│   ├── checks.py        # Custom checks
│   ├── converters.py    # Custom converters
│   ├── embeds.py        # Embed helpers
│   └── time.py          # Time utilities
│
├── database/            # Database layer
│   ├── __init__.py
│   ├── models.py       # Database models
│   ├── queries.py      # Query functions
│   └── migrations/     # Database migrations
│
├── tests/              # Unit tests
│   ├── __init__.py
│   ├── test_commands.py
│   └── test_database.py
│
└── docs/               # Documentation
    ├── STYLEGUIDE.md
    ├── ARCHITECTURE.md
    └── API.md
```

### Import Order
**MANDATORY:** Use isort to maintain this order:

```python
# 1. Standard library imports
import asyncio
import logging
from datetime import datetime
from typing import Optional

# 2. Third-party imports
import discord
from discord.ext import commands

# 3. Local imports
from config import Config
from database import Database
from utils.checks import is_moderator
```

---

## Code Structure

### Type Hints
**MANDATORY:** Use type hints for all functions:

```python
# Good
async def get_user_level(user_id: int) -> int:
    pass

async def send_embed(channel: discord.TextChannel, title: str, description: str) -> discord.Message:
    pass

def calculate_xp(level: int, multiplier: float = 1.0) -> int:
    pass

# Bad - No type hints
async def get_user_level(user_id):
    pass
```

### Docstrings
**MANDATORY:** All public functions, classes, and modules must have docstrings:

```python
def calculate_level_xp(level: int) -> int:
    """
    Calculate total XP required to reach a specific level.
    
    Args:
        level: The target level (must be positive)
    
    Returns:
        Total XP required to reach that level
    
    Raises:
        ValueError: If level is less than 1
    
    Example:
        >>> calculate_level_xp(5)
        1250
    """
    if level < 1:
        raise ValueError("Level must be at least 1")
    return (level ** 2) * 50
```

### Command Structure
```python
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
async def ban_command(
    ctx: commands.Context,
    member: discord.Member,
    *,
    reason: Optional[str] = None
) -> None:
    """
    Ban a member from the server.
    
    Args:
        member: The member to ban
        reason: Optional reason for the ban
    """
    try:
        await member.ban(reason=reason)
        await ctx.send(f"✅ {member.mention} has been banned.")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to ban this member.")
    except discord.HTTPException as e:
        logger.exception("Failed to ban member")
        await ctx.send(f"❌ Failed to ban member: {e}")
```

---

## Documentation

### Module Docstrings
```python
"""
Moderation commands for Discord server management.

This module provides commands for kicking, banning, muting, and warning users.
All commands require appropriate permissions and log actions to the audit log.

Commands:
    - kick: Remove a member from the server
    - ban: Permanently ban a member
    - mute: Temporarily mute a member
    - warn: Issue a warning to a member
"""
```

### README Requirements
Every cog folder should have a README explaining:
- Purpose of the cog
- Available commands
- Required permissions
- Configuration needed

---

## What is Forbidden

### ❌ NEVER Do This

1. **Hardcode Tokens or Secrets**
```python
# FORBIDDEN
bot.run("MTIzNDU2Nzg5MDEyMzQ1Njc4.GHiJkL.MnOpQrStUvWxYz")

# CORRECT
import os
bot.run(os.getenv("DISCORD_TOKEN"))
```

2. **Catch All Exceptions Without Logging**
```python
# FORBIDDEN
try:
    await member.ban()
except:
    pass

# CORRECT
try:
    await member.ban()
except discord.Forbidden:
    await ctx.send("Missing permissions")
except Exception:
    logger.exception("Unexpected error during ban")
    raise
```

3. **Use `time.sleep()` in Async Code**
```python
# FORBIDDEN
import time
time.sleep(5)

# CORRECT
import asyncio
await asyncio.sleep(5)
```

4. **Store Sensitive Data in Database Without Encryption**
```python
# FORBIDDEN
await db.execute("INSERT INTO users (password) VALUES (?)", (plain_password,))

# CORRECT (if needed)
import hashlib
hashed = hashlib.sha256(password.encode()).hexdigest()
await db.execute("INSERT INTO users (password_hash) VALUES (?)", (hashed,))
```

5. **Modify Mutable Default Arguments**
```python
# FORBIDDEN
def add_role(roles=[]):
    roles.append("member")
    return roles

# CORRECT
def add_role(roles=None):
    if roles is None:
        roles = []
    roles.append("member")
    return roles
```

6. **Use `eval()` or `exec()` on User Input**
```python
# FORBIDDEN - Security vulnerability
user_code = ctx.message.content
eval(user_code)

# No safe alternative for arbitrary code execution
```

7. **Create Blocking Operations**
```python
# FORBIDDEN
import requests
response = requests.get("https://api.example.com")

# CORRECT
import aiohttp
async with aiohttp.ClientSession() as session:
    async with session.get("https://api.example.com") as response:
        data = await response.json()
```

---

## What is Mandatory

### ✅ ALWAYS Do This

1. **Use Environment Variables**
```python
# .env file
DISCORD_TOKEN=your_token_here
DATABASE_URL=postgresql://...

# Load in code
from dotenv import load_dotenv
load_dotenv()
```

2. **Validate User Input**
```python
@bot.command()
async def timeout(ctx, duration: int):
    if not 1 <= duration <= 1440:  # 1 min to 24 hours
        await ctx.send("Duration must be between 1 and 1440 minutes.")
        return
    # Proceed with timeout
```

3. **Use Logging Instead of Print**
```python
# FORBIDDEN
print("Bot started")

# MANDATORY
import logging
logger = logging.getLogger(__name__)
logger.info("Bot started")
```

4. **Close Database Connections**
```python
async def setup_db():
    bot.db = await aiosqlite.connect("bot.db")

@bot.event
async def on_shutdown():
    await bot.db.close()
```

5. **Handle Rate Limits**
```python
@bot.command()
@commands.cooldown(1, 5, commands.BucketType.user)
async def daily(ctx):
    # Command code
    pass
```

6. **Check Permissions Before Actions**
```python
if ctx.guild.me.guild_permissions.manage_roles:
    await member.add_roles(role)
else:
    await ctx.send("I need 'Manage Roles' permission.")
```

---

## Error Handling

### Standard Error Handler
```python
@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError) -> None:
    """Global error handler for all commands."""
    
    # Ignore these errors
    if isinstance(error, commands.CommandNotFound):
        return
    
    # Handle specific errors with user-friendly messages
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: `{error.param.name}`")
    
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument: {error}")
    
    elif isinstance(error, commands.MissingPermissions):
        perms = ", ".join(error.missing_permissions)
        await ctx.send(f"❌ You need: {perms}")
    
    elif isinstance(error, commands.BotMissingPermissions):
        perms = ", ".join(error.missing_permissions)
        await ctx.send(f"❌ I need: {perms}")
    
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏱️ Cooldown: {error.retry_after:.1f}s")
    
    else:
        # Log unexpected errors
        logger.exception("Unhandled command error", exc_info=error)
        await ctx.send("❌ An unexpected error occurred.")
```

---

## Database Practices

### Use Parameterized Queries
```python
# FORBIDDEN - SQL injection vulnerability
user_id = ctx.author.id
await db.execute(f"SELECT * FROM users WHERE id = {user_id}")

# MANDATORY
await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### Transaction Management
```python
async def transfer_coins(from_user: int, to_user: int, amount: int):
    async with db.transaction():
        await db.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (amount, from_user))
        await db.execute("UPDATE users SET coins = coins + ? WHERE id = ?", (amount, to_user))
```

---

## Discord-Specific Rules

### Embed Limits
```python
# Respect Discord limits
MAX_EMBED_TITLE = 256
MAX_EMBED_DESCRIPTION = 4096
MAX_EMBED_FIELDS = 25
MAX_FIELD_NAME = 256
MAX_FIELD_VALUE = 1024
MAX_FOOTER = 2048
MAX_AUTHOR = 256
```

### Message Length
```python
def truncate_message(text: str, max_length: int = 2000) -> str:
    """Truncate message to fit Discord's limit."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."
```

### Intents Declaration
```python
# MANDATORY - Declare all intents used
intents = discord.Intents.default()
intents.message_content = True  # Required for reading messages
intents.members = True         # Required for member events
intents.presences = False      # Don't request if not needed

bot = commands.Bot(command_prefix="!", intents=intents)
```

---

## Code Review Checklist

Before committing, verify:
- [ ] Code formatted with Black
- [ ] Imports sorted with isort
- [ ] No flake8 warnings
- [ ] Type hints on all functions
- [ ] Docstrings on public functions
- [ ] No hardcoded secrets
- [ ] Error handling in place
- [ ] Logging instead of print
- [ ] Tests written for new features
- [ ] Documentation updated

---

## Tools Configuration

### pyproject.toml
```toml
[tool.black]
line-length = 88
target-version = ['py310']

[tool.isort]
profile = "black"
line_length = 88

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### .flake8
```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,venv,.venv
```

---

## Enforcement

### Pre-commit Hooks
Install pre-commit hooks to enforce standards:

```bash
pip install pre-commit
```

**.pre-commit-config.yaml**
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
```

```bash
pre-commit install
```

---

## Final Notes

- **Consistency is key** - Follow these rules in every file
- **When in doubt, ask** - Better to clarify than assume
- **Update this guide** - As the project evolves, update standards
- **Lead by example** - Maintainers must follow these rules first

**Remember:** These rules exist to prevent the "silent apocalypse" after months of development. Follow them religiously.
