# Command Lifecycle Documentation
**The complete journey of a Discord command from user input to response**

This document traces the entire lifecycle of commands in discord.py, helping developers understand how the bot "thinks" and processes user interactions.

---

## Table of Contents
1. [Overview](#overview)
2. [Traditional Command Lifecycle](#traditional-command-lifecycle)
3. [Slash Command Lifecycle](#slash-command-lifecycle)
4. [Event Lifecycle](#event-lifecycle)
5. [Timing Breakdown](#timing-breakdown)
6. [Debugging Lifecycle](#debugging-lifecycle)

---

## Overview

Understanding command lifecycle is crucial for:
- **Debugging** - Know where to look when something breaks
- **Optimization** - Identify bottlenecks
- **Error Handling** - Catch issues at the right stage
- **Architecture** - Design better bot systems

---

## Traditional Command Lifecycle

### Phase 1: Message Creation (Discord → Bot)

```
User types: !ban @User breaking rules
                    ↓
Discord Client sends message to Discord API
                    ↓
Discord API broadcasts MESSAGE_CREATE event
                    ↓
discord.py receives WebSocket event
                    ↓
Bot's event loop processes the event
```

**What happens:**
1. User sends message in Discord
2. Discord's backend validates and stores the message
3. WebSocket connection sends event to bot
4. Bot's internal queue receives the event

**Timing:** ~50-200ms depending on Discord's load

---

### Phase 2: Event Processing

```python
# Internal discord.py process
@bot.event
async def on_message(message: discord.Message):
    # Phase 2 starts here
    
    # 1. Bot checks if message author is itself
    if message.author.bot:
        return
    
    # 2. Process commands
    await bot.process_commands(message)
```

**What happens:**
1. `on_message` event fires
2. Bot checks if author is a bot (prevent bot loops)
3. Message passed to command processor

**Timing:** <1ms

---

### Phase 3: Command Detection

```python
# Inside bot.process_commands(message)

# 1. Check if message starts with prefix
if not message.content.startswith(bot.command_prefix):
    return  # Not a command

# 2. Extract command name
# "!ban @User reason" -> command_name = "ban"
parts = message.content[len(prefix):].split()
command_name = parts[0].lower()

# 3. Lookup command in registry
command = bot.get_command(command_name)
if command is None:
    # CommandNotFound error
    return
```

**What happens:**
1. Check for valid prefix (`!`, `?`, etc.)
2. Parse command name from message
3. Search command registry
4. If not found, raise `CommandNotFound`

**Timing:** <1ms

---

### Phase 4: Context Creation

```python
# Create Context object with all relevant information
ctx = await bot.get_context(message)

# Context contains:
# - message: Original message object
# - bot: Bot instance
# - command: Command object
# - author: Message author
# - guild: Server (if not DM)
# - channel: Channel where command was used
# - prefix: Prefix used
# - invoked_with: Exact command text used
```

**What happens:**
1. Bot creates `Context` object
2. Gathers all relevant metadata
3. Attaches helper methods (`ctx.send`, `ctx.reply`, etc.)

**Timing:** <1ms

---

### Phase 5: Checks and Validations

```python
# Run all checks in order

# 1. Global checks (applied to all commands)
for check in bot.checks:
    if not await check(ctx):
        raise CheckFailure()

# 2. Command-specific checks
@commands.has_permissions(ban_members=True)  # ← This check
@commands.bot_has_permissions(ban_members=True)  # ← And this
async def ban(ctx, member):
    pass

# 3. Cooldown checks
@commands.cooldown(1, 60, commands.BucketType.user)
async def daily(ctx):
    pass

# Each check can raise:
# - MissingPermissions
# - BotMissingPermissions
# - CheckFailure
# - CommandOnCooldown
```

**Check order:**
1. Bot checks
2. Global checks
3. Cog checks
4. Command checks
5. Cooldown checks

**What happens:**
1. Run each check function
2. If any check fails, raise exception
3. `on_command_error` handles the exception
4. Stop execution if check fails

**Timing:** 1-5ms depending on check complexity

---

### Phase 6: Argument Parsing

```python
# User typed: !ban @User breaking the rules

@bot.command()
async def ban(ctx, member: discord.Member, *, reason: str = None):
    pass

# Parsing process:
# 1. "member: discord.Member" -> Find user mention/ID/name
#    "@User" -> Converted to discord.Member object
#
# 2. "*, reason: str" -> Take rest of message as one string
#    "breaking the rules" -> reason = "breaking the rules"
#
# 3. "= None" -> If not provided, default to None
```

**Conversion process:**
```
Raw string → Converter → Python object

"@User"     → MemberConverter  → discord.Member
"123456"    → IntConverter     → int
"#channel"  → ChannelConverter → discord.TextChannel
"@Role"     → RoleConverter    → discord.Role
```

**What happens:**
1. Parse arguments from message
2. Apply type converters
3. Validate argument count
4. Raise errors if conversion fails:
   - `MissingRequiredArgument`
   - `BadArgument`
   - `TooManyArguments`

**Timing:** 5-20ms depending on converter complexity

---

### Phase 7: Command Execution

```python
@bot.command()
async def ban(ctx, member: discord.Member, *, reason: str = None):
    # Execution starts here
    
    try:
        # Perform the actual action
        await member.ban(reason=reason)
        
        # Log to database
        await db.execute(
            "INSERT INTO bans (user_id, mod_id, reason) VALUES (?, ?, ?)",
            (member.id, ctx.author.id, reason)
        )
        
        # Send response
        embed = discord.Embed(
            title="Member Banned",
            description=f"{member.mention} was banned",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason or "No reason provided")
        embed.set_footer(text=f"Banned by {ctx.author}")
        
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to ban this member.")
    
    except discord.HTTPException as e:
        logger.exception("Failed to ban member")
        await ctx.send(f"❌ Ban failed: {e}")
```

**What happens:**
1. Function executes line by line
2. External API calls (Discord, Database)
3. Error handling within function
4. Response sent to user

**Timing:** Varies greatly:
- Simple response: 50-100ms
- Database query: +20-100ms
- Discord API call: +50-200ms
- Complex computation: +100-1000ms+

---

### Phase 8: Response Delivery

```python
# ctx.send() process

await ctx.send(embed=embed)
        ↓
# 1. Validate embed/message content
#    - Check length limits
#    - Validate embed structure
#    - Check permissions
        ↓
# 2. Build HTTP request
#    - Prepare JSON payload
#    - Add authentication
        ↓
# 3. Send to Discord API
#    - POST /channels/{channel_id}/messages
        ↓
# 4. Discord processes request
#    - Validates content
#    - Stores in database
#    - Broadcasts to connected clients
        ↓
# 5. User sees message appear
```

**What happens:**
1. Bot validates response content
2. Sends HTTP request to Discord
3. Discord validates and stores
4. Discord broadcasts to clients
5. User's client displays message

**Timing:** 50-300ms

---

### Phase 9: Cleanup and Logging

```python
@bot.event
async def on_command_completion(ctx):
    """Called after command successfully completes."""
    logger.info(
        f"Command executed: {ctx.command.name} by {ctx.author} "
        f"in {ctx.guild.name if ctx.guild else 'DM'}"
    )
    
    # Update command usage statistics
    await db.execute(
        "UPDATE commands SET usage_count = usage_count + 1 WHERE name = ?",
        (ctx.command.name,)
    )
```

**What happens:**
1. `on_command_completion` event fires
2. Logging and statistics updated
3. Cleanup of temporary resources

**Timing:** 10-50ms

---

## Complete Timeline Visualization

```
TIME    PHASE                           WHAT'S HAPPENING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0ms     User Input                      User types "!ban @User spam"
        ↓
50ms    Discord Processing              Message sent to Discord servers
        ↓
100ms   WebSocket Event                 Bot receives MESSAGE_CREATE
        ↓
101ms   on_message Event                Event handler fires
        ↓
102ms   Command Detection               Bot finds "ban" command
        ↓
103ms   Context Creation                Context object created
        ↓
108ms   Permission Checks               Validates permissions
        ↓
115ms   Argument Parsing                Converts @User to Member object
        ↓
120ms   Command Execution Start         ban() function begins
        ↓
200ms   Discord API Call                member.ban() sent to Discord
        ↓
350ms   Database Log                    Ban logged to database
        ↓
400ms   Response Sent                   ctx.send() called
        ↓
550ms   Response Delivered              User sees confirmation message
        ↓
560ms   on_command_completion           Logging and cleanup
        ↓
570ms   COMPLETE                        Total execution time: ~570ms
```

---

## Slash Command Lifecycle

Slash commands follow a different but similar path:

### Phase 1: Interaction Creation

```
User types: /ban and selects options
                    ↓
Discord Client validates locally (shows errors instantly)
                    ↓
Discord API sends INTERACTION_CREATE event
                    ↓
Bot receives interaction
```

**Key difference:** Discord validates parameters BEFORE sending to bot.

---

### Phase 2: Interaction Response (3-second deadline)

```python
@bot.tree.command(name="ban")
async def ban_slash(interaction: discord.Interaction, member: discord.Member):
    # YOU HAVE 3 SECONDS TO RESPOND
    
    # Option 1: Immediate response
    await interaction.response.send_message("Banning member...")
    
    # Option 2: Defer for longer operations
    await interaction.response.defer()
    # ... do work ...
    await interaction.followup.send("Member banned!")
```

**Critical timing:**
- **Must respond within 3 seconds** or interaction fails
- Use `defer()` for operations > 3 seconds
- Use `defer(ephemeral=True)` for invisible "thinking" state

---

### Slash Command Timeline

```
TIME    PHASE                           WHAT'S HAPPENING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0ms     User Input                      User selects /ban command
        ↓
10ms    Local Validation                Discord validates parameters locally
        ↓
50ms    Interaction Sent                INTERACTION_CREATE to bot
        ↓
100ms   Bot Receives                    Interaction object created
        ↓
105ms   Checks Run                      Permission checks (faster - no parsing)
        ↓
110ms   Function Executes               ban_slash() starts
        ↓
150ms   Defer Called                    interaction.response.defer()
        ↓  (User sees "Bot is thinking...")
200ms   Discord API Call                member.ban()
        ↓
350ms   Database Log                    Log to database
        ↓
400ms   Followup Sent                   interaction.followup.send()
        ↓
500ms   COMPLETE                        User sees final message
```

**Advantages:**
- No prefix parsing
- No argument parsing (Discord does it)
- Type-safe parameters
- Better UX with dropdown/autocomplete

---

## Event Lifecycle

Events follow a simpler path:

```python
@bot.event
async def on_member_join(member):
    # Event lifecycle:
    
    # 1. Discord event occurs (member joins)
    # 2. WebSocket sends GUILD_MEMBER_ADD
    # 3. discord.py calls on_member_join()
    # 4. Your code executes
    # 5. Complete (no response needed)
    
    channel = member.guild.system_channel
    if channel:
        await channel.send(f"Welcome {member.mention}!")
```

**Key differences:**
- No command detection
- No argument parsing
- No checks (you add them manually)
- Multiple listeners can exist

---

## Timing Breakdown

### Bottlenecks to Watch

**Fast Operations (<10ms):**
- Command detection
- Context creation
- Simple checks
- In-memory operations

**Medium Operations (10-100ms):**
- Database queries (with proper indexing)
- Simple Discord API calls
- Argument converters

**Slow Operations (>100ms):**
- Complex database queries
- External API calls
- File operations
- Heavy computation

### Optimization Tips

```python
# ❌ Slow - Multiple DB calls
user = await db.get_user(user_id)
guild = await db.get_guild(guild_id)
settings = await db.get_settings(guild_id)

# ✅ Fast - Single query with JOIN
data = await db.execute("""
    SELECT u.*, g.*, s.*
    FROM users u
    JOIN guilds g ON u.guild_id = g.id
    JOIN settings s ON g.id = s.guild_id
    WHERE u.id = ? AND g.id = ?
""", (user_id, guild_id))

# ❌ Slow - Sequential API calls
msg1 = await ctx.send("Part 1")
msg2 = await ctx.send("Part 2")
msg3 = await ctx.send("Part 3")

# ✅ Fast - Parallel API calls (if order doesn't matter)
await asyncio.gather(
    ctx.send("Part 1"),
    ctx.send("Part 2"),
    ctx.send("Part 3")
)
```

---

## Debugging Lifecycle

### Add Lifecycle Logging

```python
import logging
import time

logger = logging.getLogger(__name__)

class LifecycleLogger(commands.Cog):
    """Log every phase of command execution."""
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        logger.debug(f"[PHASE 1] Message received: {message.content[:50]}")
    
    @commands.Cog.listener()
    async def on_command(self, ctx):
        ctx.start_time = time.time()
        logger.debug(f"[PHASE 3] Command detected: {ctx.command.name}")
    
    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        duration = (time.time() - ctx.start_time) * 1000
        logger.info(
            f"[COMPLETE] {ctx.command.name} executed in {duration:.2f}ms "
            f"by {ctx.author} in {ctx.guild}"
        )
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        duration = (time.time() - ctx.start_time) * 1000
        logger.error(
            f"[ERROR] {ctx.command.name} failed after {duration:.2f}ms: {error}"
        )
```

### Profiling Commands

```python
import cProfile
import pstats
from io import StringIO

@bot.command()
@commands.is_owner()
async def profile(ctx, command_name: str):
    """Profile a command's performance."""
    
    cmd = bot.get_command(command_name)
    if not cmd:
        await ctx.send("Command not found")
        return
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Run command with profiling
    profiler.enable()
    await ctx.invoke(cmd)
    profiler.disable()
    
    # Get results
    stream = StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
    
    # Send results
    await ctx.send(f"```\n{stream.getvalue()[:1900]}\n```")
```

---

## Common Lifecycle Issues

### Issue 1: Command Not Responding

**Problem:** User runs command, nothing happens.

**Debug steps:**
1. Check if `on_message` fires → Add logging
2. Check if command is registered → Use `bot.get_command()`
3. Check if checks fail silently → Add error handler
4. Check if exception is raised → View logs

### Issue 2: Slow Response

**Problem:** Command takes too long.

**Debug steps:**
1. Add timing logs at each phase
2. Identify bottleneck (usually DB or API)
3. Optimize slow operations
4. Consider `defer()` for slash commands

### Issue 3: Interaction Failed

**Problem:** Slash command shows "Interaction failed".

**Cause:** Didn't respond within 3 seconds.

**Solution:**
```python
@bot.tree.command()
async def slow_command(interaction):
    await interaction.response.defer()  # Buy more time
    # ... long operation ...
    await interaction.followup.send("Done!")
```

---

## Lifecycle Best Practices

1. **Always respond within time limits**
   - Traditional: No hard limit, but don't make users wait
   - Slash: 3 seconds for initial response

2. **Use appropriate response methods**
   - `ctx.send()` for traditional commands
   - `interaction.response.send_message()` for slash commands
   - `defer()` for long operations

3. **Handle errors at the right level**
   - Function-level: Specific errors (Forbidden, NotFound)
   - Global: Generic errors (CommandError)

4. **Log lifecycle events**
   - Helps debugging
   - Monitors performance
   - Tracks usage

5. **Optimize bottlenecks**
   - Profile slow commands
   - Cache frequent queries
   - Use async operations

---

## Summary

Understanding command lifecycle helps you:
- **Debug faster** - Know where to look
- **Write better code** - Understand implications
- **Optimize performance** - Identify bottlenecks
- **Handle errors properly** - Catch at right phase

**Remember:** Every command follows this path. Master it, and you master the bot.
