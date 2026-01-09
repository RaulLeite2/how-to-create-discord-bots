# Permissions System Documentation
**Complete guide to Discord and bot permission management**

This document explains how permissions work in Discord bots, including hierarchies, checks, and best practices for secure permission management.

---

## Table of Contents
1. [Discord Permission System](#discord-permission-system)
2. [Bot Permission Checks](#bot-permission-checks)
3. [User Permission Checks](#user-permission-checks)
4. [Custom Permission Systems](#custom-permission-systems)
5. [Permission Hierarchy](#permission-hierarchy)
6. [Common Patterns](#common-patterns)
7. [Security Best Practices](#security-best-practices)

---

## Discord Permission System

### Understanding Discord Permissions

Discord uses a **bitwise permission system** where each permission is a bit flag.

```python
# Permission values (powers of 2)
CREATE_INSTANT_INVITE = 1 << 0    # 1
KICK_MEMBERS = 1 << 1              # 2
BAN_MEMBERS = 1 << 2               # 4
ADMINISTRATOR = 1 << 3             # 8
MANAGE_CHANNELS = 1 << 4           # 16
# ... and so on
```

### Permission Levels

**Channel → Role → User (Highest wins)**

```
1. Base Role Permissions
   └─ What the @everyone role can do

2. Role Permissions
   └─ Additional permissions from assigned roles

3. Channel Overwrites
   └─ Specific allow/deny for channels

4. Administrator Override
   └─ ADMINISTRATOR permission bypasses all checks
```

---

## Bot Permission Checks

### Checking Bot Permissions

```python
@bot.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    # Check if bot has permission in THIS guild
    if not ctx.guild.me.guild_permissions.ban_members:
        await ctx.send("❌ I don't have Ban Members permission!")
        return
    
    # Check if bot has permission in THIS channel
    if not ctx.channel.permissions_for(ctx.guild.me).send_messages:
        # Can't even send error message!
        return
    
    await member.ban(reason=reason)
    await ctx.send(f"✅ Banned {member}")
```

### Using Built-in Decorators

```python
@bot.command()
@commands.bot_has_permissions(ban_members=True, send_messages=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    """Bot checks are automatic - raises BotMissingPermissions if fails."""
    await member.ban(reason=reason)
    await ctx.send(f"✅ Banned {member}")
```

### Permission Comparison

```python
# Get bot's permissions in a channel
bot_perms = channel.permissions_for(guild.me)

# Check specific permission
if bot_perms.manage_roles:
    print("Bot can manage roles")

# Check multiple permissions
if bot_perms.manage_roles and bot_perms.manage_channels:
    print("Bot can manage roles AND channels")

# Get all granted permissions
granted = [perm for perm, value in bot_perms if value]
print(f"Bot has: {', '.join(granted)}")
```

---

## User Permission Checks

### Basic User Checks

```python
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Requires user to have Kick Members permission."""
    await member.kick(reason=reason)
    await ctx.send(f"✅ Kicked {member}")
```

### Multiple Permission Checks

```python
@bot.command()
@commands.has_permissions(
    manage_messages=True,
    manage_channels=True,
    manage_roles=True
)
async def setup(ctx):
    """Requires ALL three permissions."""
    await ctx.send("Setting up server...")
```

### Guild Owner Check

```python
@bot.command()
@commands.is_owner()  # Bot owner only
async def shutdown(ctx):
    """Only bot owner can use this."""
    await ctx.send("Shutting down...")
    await bot.close()

@bot.command()
async def transfer_ownership(ctx):
    """Only guild owner can use this."""
    if ctx.author.id != ctx.guild.owner_id:
        await ctx.send("❌ Only server owner can do this!")
        return
    
    # Transfer logic here
```

---

## Custom Permission Systems

### Role-Based Permissions

```python
# config.py or database
MODERATOR_ROLES = {
    123456789: [987654321, 876543210],  # guild_id: [role_ids]
}

def is_moderator():
    """Custom check for moderator role."""
    async def predicate(ctx):
        if not ctx.guild:
            return False
        
        guild_mod_roles = MODERATOR_ROLES.get(ctx.guild.id, [])
        user_role_ids = [role.id for role in ctx.author.roles]
        
        return any(role_id in guild_mod_roles for role_id in user_role_ids)
    
    return commands.check(predicate)

@bot.command()
@is_moderator()
async def warn(ctx, member: discord.Member):
    """Only users with moderator role can warn."""
    await ctx.send(f"⚠️ {member.mention} has been warned!")
```

### Database-Driven Permissions

```python
class PermissionManager:
    """Manage custom permissions in database."""
    
    @staticmethod
    async def has_permission(user_id: int, guild_id: int, permission: str) -> bool:
        """Check if user has custom permission."""
        result = await db.fetchone("""
            SELECT 1 FROM user_permissions
            WHERE user_id = ? AND guild_id = ? AND permission = ?
        """, (user_id, guild_id, permission))
        return result is not None
    
    @staticmethod
    async def grant_permission(user_id: int, guild_id: int, permission: str):
        """Grant custom permission to user."""
        await db.execute("""
            INSERT OR IGNORE INTO user_permissions (user_id, guild_id, permission)
            VALUES (?, ?, ?)
        """, (user_id, guild_id, permission))
    
    @staticmethod
    async def revoke_permission(user_id: int, guild_id: int, permission: str):
        """Revoke custom permission from user."""
        await db.execute("""
            DELETE FROM user_permissions
            WHERE user_id = ? AND guild_id = ? AND permission = ?
        """, (user_id, guild_id, permission))

# Custom check using database
def has_custom_permission(permission: str):
    """Check custom permission from database."""
    async def predicate(ctx):
        return await PermissionManager.has_permission(
            ctx.author.id,
            ctx.guild.id if ctx.guild else 0,
            permission
        )
    return commands.check(predicate)

@bot.command()
@has_custom_permission("manage_economy")
async def add_coins(ctx, member: discord.Member, amount: int):
    """Requires custom 'manage_economy' permission."""
    # Add coins logic
    await ctx.send(f"✅ Added {amount} coins to {member}")
```

### Permission Levels

```python
class PermissionLevel:
    """Permission level system."""
    USER = 0
    TRUSTED = 1
    MODERATOR = 2
    ADMIN = 3
    OWNER = 4

async def get_permission_level(member: discord.Member) -> int:
    """Determine user's permission level."""
    
    # Owner has highest level
    if member.id == member.guild.owner_id:
        return PermissionLevel.OWNER
    
    # Check Discord permissions
    if member.guild_permissions.administrator:
        return PermissionLevel.ADMIN
    
    if member.guild_permissions.manage_messages:
        return PermissionLevel.MODERATOR
    
    # Check database for trusted status
    is_trusted = await db.fetchone(
        "SELECT 1 FROM trusted_users WHERE user_id = ? AND guild_id = ?",
        (member.id, member.guild.id)
    )
    if is_trusted:
        return PermissionLevel.TRUSTED
    
    return PermissionLevel.USER

def requires_level(level: int):
    """Require minimum permission level."""
    async def predicate(ctx):
        user_level = await get_permission_level(ctx.author)
        if user_level < level:
            await ctx.send(f"❌ This command requires permission level {level}+")
            return False
        return True
    return commands.check(predicate)

@bot.command()
@requires_level(PermissionLevel.MODERATOR)
async def mute(ctx, member: discord.Member):
    """Requires moderator level or higher."""
    # Mute logic
    pass
```

---

## Permission Hierarchy

### Role Hierarchy

```python
@bot.command()
@commands.has_permissions(manage_roles=True)
async def add_role(ctx, member: discord.Member, role: discord.Role):
    """Add role to member - respects hierarchy."""
    
    # Check if role is above bot's highest role
    if role >= ctx.guild.me.top_role:
        await ctx.send(f"❌ Role {role} is above my highest role!")
        return
    
    # Check if role is above command user's highest role
    if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        await ctx.send(f"❌ Role {role} is above your highest role!")
        return
    
    # Check if target is above command user
    if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
        await ctx.send(f"❌ {member} has a role equal to or above yours!")
        return
    
    await member.add_roles(role)
    await ctx.send(f"✅ Added {role} to {member}")
```

### Moderation Hierarchy

```python
def can_moderate(moderator: discord.Member, target: discord.Member) -> bool:
    """Check if moderator can moderate target."""
    
    # Can't moderate owner
    if target.id == target.guild.owner_id:
        return False
    
    # Owner can moderate anyone
    if moderator.id == moderator.guild.owner_id:
        return True
    
    # Compare top roles
    return moderator.top_role > target.top_role

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Kick member - respects hierarchy."""
    
    if not can_moderate(ctx.author, member):
        await ctx.send("❌ You cannot kick this member (role hierarchy)")
        return
    
    if not can_moderate(ctx.guild.me, member):
        await ctx.send("❌ I cannot kick this member (role hierarchy)")
        return
    
    await member.kick(reason=reason)
    await ctx.send(f"✅ Kicked {member}")
```

---

## Common Patterns

### Combined Checks

```python
from discord.ext import commands

def is_mod_or_admin():
    """Check if user is moderator or admin."""
    async def predicate(ctx):
        # Admin check
        if ctx.author.guild_permissions.administrator:
            return True
        
        # Moderator check
        if ctx.author.guild_permissions.manage_messages:
            return True
        
        # Custom role check
        mod_role = discord.utils.get(ctx.guild.roles, name="Moderator")
        if mod_role in ctx.author.roles:
            return True
        
        return False
    
    return commands.check(predicate)

@bot.command()
@is_mod_or_admin()
async def clear(ctx, amount: int):
    """Clear messages - mods or admins only."""
    await ctx.channel.purge(limit=amount)
```

### Guild-Only Commands

```python
@bot.command()
@commands.guild_only()  # Fails in DMs
async def server_info(ctx):
    """Show server info - guild only."""
    embed = discord.Embed(title=ctx.guild.name)
    embed.add_field(name="Members", value=ctx.guild.member_count)
    await ctx.send(embed=embed)
```

### DM-Only Commands

```python
@bot.command()
@commands.dm_only()  # Fails in guilds
async def profile(ctx):
    """Show user profile - DM only for privacy."""
    # Profile logic
    pass
```

### NSFW Channel Check

```python
@bot.command()
@commands.is_nsfw()  # Requires NSFW channel
async def nsfw_command(ctx):
    """Only works in NSFW channels."""
    pass
```

---

## Security Best Practices

### 1. Always Check Both User and Bot

```python
@bot.command()
@commands.has_permissions(ban_members=True)  # User check
@commands.bot_has_permissions(ban_members=True)  # Bot check
async def ban(ctx, member: discord.Member):
    """Both checks prevent confusing errors."""
    await member.ban()
```

### 2. Validate Role Hierarchy

```python
@bot.command()
async def promote(ctx, member: discord.Member, role: discord.Role):
    """Always validate hierarchy before role operations."""
    
    # All the hierarchy checks
    if role >= ctx.guild.me.top_role:
        await ctx.send("❌ That role is above my highest role")
        return
    
    if role >= ctx.author.top_role and not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ That role is above your highest role")
        return
    
    await member.add_roles(role)
```

### 3. Protect Dangerous Commands

```python
@bot.command()
@commands.is_owner()  # Bot owner only
@commands.guild_only()
async def nuke(ctx):
    """Extremely dangerous command - extra confirmation."""
    
    await ctx.send("⚠️ This will delete ALL channels. Type `CONFIRM` to proceed.")
    
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel and m.content == "CONFIRM"
    
    try:
        await bot.wait_for('message', check=check, timeout=30.0)
    except asyncio.TimeoutError:
        await ctx.send("❌ Cancelled")
        return
    
    # Dangerous operation
    for channel in ctx.guild.channels:
        await channel.delete()
```

### 4. Log Permission-Based Actions

```python
@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    """Log all moderation actions."""
    
    # Perform action
    await member.kick(reason=reason)
    
    # Log to database
    await db.execute("""
        INSERT INTO mod_actions (guild_id, mod_id, target_id, action, reason)
        VALUES (?, ?, ?, ?, ?)
    """, (ctx.guild.id, ctx.author.id, member.id, "kick", reason))
    
    # Log to channel
    log_channel = ctx.guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title="Member Kicked", color=discord.Color.orange())
        embed.add_field(name="Member", value=f"{member} ({member.id})")
        embed.add_field(name="Moderator", value=f"{ctx.author} ({ctx.author.id})")
        embed.add_field(name="Reason", value=reason or "No reason provided")
        embed.timestamp = discord.utils.utcnow()
        await log_channel.send(embed=embed)
    
    await ctx.send(f"✅ Kicked {member}")
```

### 5. Rate Limit Dangerous Commands

```python
@bot.command()
@commands.has_permissions(manage_messages=True)
@commands.cooldown(1, 60, commands.BucketType.user)  # 1 per minute per user
async def purge(ctx, amount: int):
    """Rate limit to prevent abuse."""
    
    if amount > 100:
        await ctx.send("❌ Maximum 100 messages at once")
        return
    
    await ctx.channel.purge(limit=amount)
```

---

## Error Handling

### Permission Error Handler

```python
@bot.event
async def on_command_error(ctx, error):
    """Handle permission errors gracefully."""
    
    if isinstance(error, commands.MissingPermissions):
        missing = ", ".join(error.missing_permissions)
        await ctx.send(f"❌ You need these permissions: {missing}")
    
    elif isinstance(error, commands.BotMissingPermissions):
        missing = ", ".join(error.missing_permissions)
        await ctx.send(f"❌ I need these permissions: {missing}")
    
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command")
    
    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send("❌ This command cannot be used in DMs")
    
    elif isinstance(error, commands.PrivateMessageOnly):
        await ctx.send("❌ This command can only be used in DMs")
    
    else:
        logger.exception("Unhandled error", exc_info=error)
```

---

## Permission Audit System

```python
@bot.command()
@commands.has_permissions(administrator=True)
async def audit_permissions(ctx):
    """Audit all role permissions in the server."""
    
    embed = discord.Embed(title="Permission Audit", color=discord.Color.blue())
    
    for role in sorted(ctx.guild.roles, reverse=True):
        dangerous_perms = []
        
        if role.permissions.administrator:
            dangerous_perms.append("Administrator")
        if role.permissions.manage_guild:
            dangerous_perms.append("Manage Server")
        if role.permissions.manage_roles:
            dangerous_perms.append("Manage Roles")
        if role.permissions.manage_channels:
            dangerous_perms.append("Manage Channels")
        if role.permissions.kick_members:
            dangerous_perms.append("Kick Members")
        if role.permissions.ban_members:
            dangerous_perms.append("Ban Members")
        
        if dangerous_perms:
            embed.add_field(
                name=f"{role.name}",
                value=", ".join(dangerous_perms),
                inline=False
            )
    
    await ctx.send(embed=embed)
```

---

## Summary

**Permission Hierarchy:**
```
1. Administrator (bypasses everything)
2. Guild Owner (can do anything)
3. Role Permissions
4. Channel Overwrites
5. Default @everyone
```

**Best Practices:**
- ✅ Always check both user AND bot permissions
- ✅ Respect role hierarchy
- ✅ Use built-in decorators when possible
- ✅ Log permission-based actions
- ✅ Handle errors gracefully
- ✅ Rate limit dangerous commands
- ✅ Add confirmation for destructive actions

**Remember:** Permissions exist to protect your server. Never bypass them without good reason.
