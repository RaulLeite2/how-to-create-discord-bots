# Contributing Guide
**How to add commands, cogs, tables, and checks without breaking anything**

This guide defines the process for contributing to the bot. Follow these steps to maintain code quality and prevent issues.

---

## Table of Contents
1. [Getting Started](#getting-started)
2. [Adding Commands](#adding-commands)
3. [Creating Cogs](#creating-cogs)
4. [Database Changes](#database-changes)
5. [Adding Checks](#adding-checks)
6. [Testing](#testing)
7. [Pull Request Process](#pull-request-process)
8. [Code Review Checklist](#code-review-checklist)

---

## Getting Started

### Prerequisites

1. **Fork and Clone**
```bash
git clone https://github.com/yourusername/discord-bot
cd discord-bot
```

2. **Setup Environment**
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Testing tools
```

3. **Configure Bot**
```bash
# Copy example environment
cp .env.example .env

# Edit .env with your bot token and settings
```

4. **Initialize Database**
```bash
# Run migrations
python -m bot.database.migrate
```

5. **Create Feature Branch**
```bash
git checkout -b feature/your-feature-name
```

---

## Adding Commands

### Process Overview

```
1. Choose appropriate cog
2. Write command function
3. Add type hints and docstrings
4. Add permission checks
5. Add error handling
6. Write tests
7. Update documentation
8. Submit PR
```

### Step-by-Step: Adding a Command

#### 1. Choose or Create Cog

```python
# If adding to existing cog, open the file
# cogs/moderation.py

# If creating new cog, use template:
# cogs/your_feature.py
```

#### 2. Write Command Function

```python
from discord.ext import commands
import discord
from typing import Optional

class ModerationCog(commands.Cog):
    """Moderation commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(send_messages=True)
    async def warn_member(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: Optional[str] = None
    ) -> None:
        """
        Issue a warning to a member.
        
        Args:
            member: The member to warn
            reason: Reason for the warning (optional)
        
        Example:
            !warn @User Spamming in chat
        """
        # Validate: Can't warn yourself
        if member.id == ctx.author.id:
            await ctx.send("❌ You cannot warn yourself!")
            return
        
        # Validate: Can't warn bots
        if member.bot:
            await ctx.send("❌ You cannot warn bots!")
            return
        
        # Validate: Respect hierarchy
        if member.top_role >= ctx.author.top_role:
            await ctx.send("❌ You cannot warn someone with a role equal to or higher than yours!")
            return
        
        try:
            # Add to database
            await self.bot.db.execute("""
                INSERT INTO warnings (user_id, guild_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
            """, (member.id, ctx.guild.id, ctx.author.id, reason))
            
            # Get warning count
            count = await self.bot.db.fetchone("""
                SELECT COUNT(*) as count FROM warnings
                WHERE user_id = ? AND guild_id = ? AND active = TRUE
            """, (member.id, ctx.guild.id))
            
            # Send response
            embed = discord.Embed(
                title="⚠️ Member Warned",
                color=discord.Color.orange()
            )
            embed.add_field(name="Member", value=member.mention)
            embed.add_field(name="Reason", value=reason or "No reason provided")
            embed.add_field(name="Total Warnings", value=count['count'])
            embed.set_footer(text=f"Warned by {ctx.author}")
            
            await ctx.send(embed=embed)
            
            # DM the user
            try:
                dm_embed = discord.Embed(
                    title=f"⚠️ Warning in {ctx.guild.name}",
                    description=f"You have been warned by {ctx.author}",
                    color=discord.Color.orange()
                )
                dm_embed.add_field(name="Reason", value=reason or "No reason provided")
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled
            
        except Exception as e:
            self.bot.logger.exception("Failed to warn member")
            await ctx.send(f"❌ Failed to warn member: {e}")

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
```

#### 3. Command Checklist

**Before submitting, verify:**

- ✅ Type hints on all parameters
- ✅ Docstring with description and examples
- ✅ Permission checks (user and bot)
- ✅ Input validation
- ✅ Error handling (try/except)
- ✅ User feedback (success and error messages)
- ✅ Logging for debugging
- ✅ Follows naming conventions (see STYLEGUIDE.md)

---

## Creating Cogs

### Cog Template

```python
"""
Description of what this cog does.

Commands:
    - command1: Brief description
    - command2: Brief description
"""

import discord
from discord.ext import commands
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class YourFeatureCog(commands.Cog):
    """Brief description of the cog."""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        logger.info("YourFeatureCog initialized")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Called when cog is ready."""
        logger.info("YourFeatureCog ready")
    
    @commands.command(name="yourcommand")
    async def your_command(self, ctx: commands.Context):
        """
        Brief description of command.
        
        Example:
            !yourcommand
        """
        await ctx.send("Command executed!")
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        Listen to message events if needed.
        
        Note: Be careful with message listeners - they fire for EVERY message!
        """
        if message.author.bot:
            return
        
        # Your logic here


async def setup(bot: commands.Bot):
    """Required function to load the cog."""
    await bot.add_cog(YourFeatureCog(bot))
```

### Registering Cog

Cogs are automatically loaded from the `cogs/` directory if your `main.py` has:

```python
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'cogs.{filename[:-3]}')
```

---

## Database Changes

### CRITICAL: Never Modify Tables Directly

❌ **WRONG:**
```sql
-- Don't do this in production!
ALTER TABLE users ADD COLUMN new_field TEXT;
```

✅ **CORRECT: Use Migrations**

### Creating a Migration

#### 1. Create Migration File

```bash
# Naming: {version}_{description}.sql
# migrations/004_add_user_badges.sql
```

#### 2. Write Migration SQL

```sql
-- migrations/004_add_user_badges.sql

-- Add new table
CREATE TABLE user_badges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    badge_name TEXT NOT NULL,
    awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, badge_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Create index
CREATE INDEX idx_user_badges_user ON user_badges(user_id);

-- Update schema version
UPDATE schema_version SET version = 4;
```

#### 3. Write Rollback (Optional but Recommended)

```sql
-- migrations/004_add_user_badges_rollback.sql

DROP TABLE IF EXISTS user_badges;
UPDATE schema_version SET version = 3;
```

#### 4. Test Migration Locally

```bash
# Backup first!
cp bot.db bot.db.backup

# Run migration
python -m bot.database.migrate

# Test that everything works

# If problems, rollback
python -m bot.database.rollback
```

#### 5. Document in DATABASE.md

Update `DATABASE.md` with:
- Table description
- What it represents
- When it grows
- When it's cleaned
- Who can touch it
- Example queries

### Migration Checklist

- ✅ Migration file numbered sequentially
- ✅ Descriptive filename
- ✅ Includes indexes for common queries
- ✅ Updates schema_version
- ✅ Tested on local database
- ✅ Rollback script written (optional)
- ✅ DATABASE.md updated
- ✅ Code updated to use new schema

---

## Adding Checks

### Custom Check Template

```python
# utils/checks.py

from discord.ext import commands
from typing import Callable

def is_moderator() -> Callable:
    """
    Check if user is a moderator.
    
    Moderator criteria:
    - Has Manage Messages permission, OR
    - Has "Moderator" role, OR
    - Is guild owner
    """
    async def predicate(ctx: commands.Context) -> bool:
        # Owner always passes
        if ctx.author.id == ctx.guild.owner_id:
            return True
        
        # Check Discord permissions
        if ctx.author.guild_permissions.manage_messages:
            return True
        
        # Check for moderator role
        mod_role = discord.utils.get(ctx.guild.roles, name="Moderator")
        if mod_role and mod_role in ctx.author.roles:
            return True
        
        return False
    
    return commands.check(predicate)


def has_voted() -> Callable:
    """
    Check if user has voted for the bot recently.
    
    Uses external API or database to verify vote status.
    """
    async def predicate(ctx: commands.Context) -> bool:
        # Check database for recent vote
        result = await ctx.bot.db.fetchone("""
            SELECT voted_at FROM votes
            WHERE user_id = ?
              AND voted_at > datetime('now', '-12 hours')
        """, (ctx.author.id,))
        
        if result:
            return True
        
        await ctx.send("❌ You need to vote for the bot to use this command! <vote_link>")
        return False
    
    return commands.check(predicate)


def in_bot_channel() -> Callable:
    """
    Check if command is used in designated bot channel.
    """
    async def predicate(ctx: commands.Context) -> bool:
        # Get bot channel from config
        config = await ctx.bot.db.fetchone(
            "SELECT bot_channel_id FROM guild_config WHERE guild_id = ?",
            (ctx.guild.id,)
        )
        
        if not config or not config['bot_channel_id']:
            return True  # No restriction if not configured
        
        if ctx.channel.id == config['bot_channel_id']:
            return True
        
        bot_channel = ctx.guild.get_channel(config['bot_channel_id'])
        await ctx.send(f"❌ This command can only be used in {bot_channel.mention}")
        return False
    
    return commands.check(predicate)
```

### Using Custom Checks

```python
from utils.checks import is_moderator, has_voted, in_bot_channel

@bot.command()
@is_moderator()
async def clear(ctx, amount: int):
    """Moderators only - clear messages."""
    await ctx.channel.purge(limit=amount)

@bot.command()
@has_voted()
@in_bot_channel()
async def daily(ctx):
    """Requires vote and must be in bot channel."""
    # Daily reward logic
    pass
```

---

## Testing

### Unit Tests

```python
# tests/test_moderation.py

import pytest
from unittest.mock import AsyncMock, MagicMock
from cogs.moderation import ModerationCog

@pytest.mark.asyncio
async def test_warn_command():
    """Test warn command basic functionality."""
    
    # Mock bot and database
    bot = MagicMock()
    bot.db.execute = AsyncMock()
    bot.db.fetchone = AsyncMock(return_value={'count': 1})
    
    # Create cog
    cog = ModerationCog(bot)
    
    # Mock context
    ctx = MagicMock()
    ctx.author.id = 123
    ctx.guild.id = 456
    ctx.send = AsyncMock()
    
    # Mock member
    member = MagicMock()
    member.id = 789
    member.bot = False
    member.top_role = MagicMock(position=1)
    ctx.author.top_role = MagicMock(position=2)
    
    # Execute command
    await cog.warn_member(ctx, member, reason="Test warning")
    
    # Verify database call
    bot.db.execute.assert_called_once()
    
    # Verify response
    ctx.send.assert_called_once()

@pytest.mark.asyncio
async def test_warn_self():
    """Test that users cannot warn themselves."""
    
    bot = MagicMock()
    cog = ModerationCog(bot)
    
    ctx = MagicMock()
    ctx.author.id = 123
    ctx.send = AsyncMock()
    
    member = MagicMock()
    member.id = 123  # Same as author
    
    await cog.warn_member(ctx, member)
    
    # Verify error message
    assert "cannot warn yourself" in str(ctx.send.call_args)
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=cogs --cov=utils

# Run specific test file
pytest tests/test_moderation.py

# Run specific test
pytest tests/test_moderation.py::test_warn_command
```

---

## Pull Request Process

### 1. Before Opening PR

- ✅ All tests pass locally
- ✅ Code formatted (Black)
- ✅ Imports sorted (isort)
- ✅ No linter warnings (flake8)
- ✅ Type hints added (mypy)
- ✅ Documentation updated
- ✅ CHANGELOG.md updated

### 2. Commit Messages

Use conventional commits:

```bash
git commit -m "feat: add warn command to moderation cog"
git commit -m "fix: resolve role hierarchy bug in warn command"
git commit -m "docs: update DATABASE.md with new badges table"
git commit -m "test: add unit tests for warn command"
```

### 3. PR Title and Description

**Good PR Title:**
```
feat: Add warning system to moderation cog
```

**Good PR Description:**
```markdown
## Description
Adds a comprehensive warning system for moderators.

## Changes
- Added `warn` command to ModerationCog
- Created `warnings` database table (migration 004)
- Added tests for warn functionality
- Updated PERMISSIONS.md with warning permissions

## Testing
- [x] Tested warning creation
- [x] Tested warning retrieval
- [x] Tested permission checks
- [x] Tested role hierarchy
- [x] All unit tests pass

## Screenshots
[Attach screenshots of command in action]

## Checklist
- [x] Code follows STYLEGUIDE.md
- [x] Tests added and passing
- [x] Documentation updated
- [x] Migration tested locally
```

### 4. Code Review

Be responsive to feedback:
- Answer questions promptly
- Make requested changes
- Don't take criticism personally
- Learn from suggestions

---

## Code Review Checklist

### For Reviewers

**Functionality:**
- [ ] Does it work as intended?
- [ ] Are edge cases handled?
- [ ] Is error handling comprehensive?

**Code Quality:**
- [ ] Follows STYLEGUIDE.md?
- [ ] Type hints present?
- [ ] Docstrings clear?
- [ ] No code duplication?

**Security:**
- [ ] Input validation present?
- [ ] SQL injection prevented?
- [ ] Permissions checked properly?
- [ ] Rate limits appropriate?

**Performance:**
- [ ] No unnecessary database queries?
- [ ] Async/await used correctly?
- [ ] No blocking operations?

**Testing:**
- [ ] Tests added?
- [ ] Tests comprehensive?
- [ ] Tests passing?

**Documentation:**
- [ ] DATABASE.md updated (if schema changed)?
- [ ] README.md updated (if needed)?
- [ ] CHANGELOG.md updated?

---

## Common Mistakes to Avoid

### ❌ Don't Do This

1. **Modifying database without migration**
```python
# DON'T
await db.execute("ALTER TABLE users ADD COLUMN badges TEXT")
```

2. **Forgetting permission checks**
```python
# DON'T
@bot.command()
async def ban(ctx, member):
    await member.ban()  # No permission check!
```

3. **Not handling errors**
```python
# DON'T
@bot.command()
async def kick(ctx, member):
    await member.kick()  # What if it fails?
    await ctx.send("Kicked!")
```

4. **Hardcoding values**
```python
# DON'T
if ctx.channel.id == 123456789:  # Hard-coded channel ID
```

5. **Blocking operations in async context**
```python
# DON'T
import time
time.sleep(5)  # Blocks entire bot!
```

### ✅ Do This Instead

1. **Use migrations**
2. **Always check permissions**
3. **Handle all errors**
4. **Use configuration**
5. **Use async sleep**

---

## Getting Help

**Have questions?**
- Check existing documentation first
- Read the code - it's documented!
- Ask in #development channel (Discord)
- Open a discussion (GitHub)

**Found a bug?**
- Open an issue with reproduction steps
- Include error logs
- Include your environment details

**Want to propose a feature?**
- Open a discussion first
- Explain the use case
- Consider breaking it into smaller PRs

---

## Thank You!

Your contributions make this bot better for everyone. Take your time, follow the guidelines, and don't hesitate to ask questions.

**Remember:** It's better to ask before coding than to redo work after. We're here to help!
