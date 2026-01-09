# Database Documentation
**Schema, meaning, and lifecycle of bot data**

This document explains what each database table represents, when it grows, when it's cleaned, and who can modify it. Without this, your database becomes tribal knowledge within months.

---

## Table of Contents
1. [Database Philosophy](#database-philosophy)
2. [Schema Overview](#schema-overview)
3. [Table Documentation](#table-documentation)
4. [Data Lifecycle](#data-lifecycle)
5. [Maintenance](#maintenance)
6. [Migration Strategy](#migration-strategy)
7. [Backup and Recovery](#backup-and-recovery)

---

## Database Philosophy

### Design Principles

**1. Data has meaning beyond its structure**
- Tables aren't just columns - they represent concepts in your bot's world
- Every table tells a story about user behavior or bot state

**2. Growth is inevitable**
- Plan for millions of rows, not hundreds
- Index appropriately from day one
- Consider archiving strategies

**3. Cleanup is mandatory**
- Data grows forever unless you actively clean it
- Define retention policies upfront
- Automated cleanup prevents database bloat

**4. Access control matters**
- Not all code should touch all tables
- Define clear ownership and responsibilities
- Document who can modify what

---

## Schema Overview

### Technology Stack

**SQLite (Development/Small Bots)**
```bash
# Advantages: Zero configuration, portable
# Disadvantages: Limited concurrency, no remote access
# Good for: <1000 active users
```

**PostgreSQL (Production/Large Bots)**
```bash
# Advantages: Concurrent, scalable, rich features
# Disadvantages: Requires server, more complex
# Good for: >1000 active users
```

### Complete Schema

```sql
-- Users: Core user data across all guilds
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    username TEXT NOT NULL,
    global_xp INTEGER DEFAULT 0,
    global_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Guild Members: User data specific to each guild
CREATE TABLE guild_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    coins INTEGER DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, guild_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Guild Configuration: Per-server settings
CREATE TABLE guild_config (
    guild_id BIGINT PRIMARY KEY,
    prefix TEXT DEFAULT '!',
    welcome_channel_id BIGINT,
    log_channel_id BIGINT,
    mute_role_id BIGINT,
    auto_role_id BIGINT,
    xp_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Moderation Warnings: User infractions
CREATE TABLE warnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- Moderation Actions: Complete mod action log
CREATE TABLE mod_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id BIGINT NOT NULL,
    moderator_id BIGINT NOT NULL,
    target_id BIGINT NOT NULL,
    action_type TEXT NOT NULL, -- kick, ban, mute, warn, unmute, unban
    reason TEXT,
    duration INTEGER, -- Duration in seconds for temporary actions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Temporary Punishments: Active mutes, bans with expiry
CREATE TABLE temp_punishments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    punishment_type TEXT NOT NULL, -- mute, ban
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, guild_id, punishment_type)
);

-- Economy Transactions: Money movement history
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    guild_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,
    transaction_type TEXT NOT NULL, -- daily, work, gamble, transfer, purchase
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom Commands: User-created server commands
CREATE TABLE custom_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id BIGINT NOT NULL,
    command_name TEXT NOT NULL,
    response TEXT NOT NULL,
    creator_id BIGINT NOT NULL,
    uses INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(guild_id, command_name)
);

-- Reminders: User-scheduled reminders
CREATE TABLE reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    message TEXT NOT NULL,
    remind_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed BOOLEAN DEFAULT FALSE
);

-- Command Stats: Usage analytics
CREATE TABLE command_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_name TEXT NOT NULL,
    guild_id BIGINT,
    user_id BIGINT NOT NULL,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for common queries
CREATE INDEX idx_guild_members_guild ON guild_members(guild_id);
CREATE INDEX idx_guild_members_user ON guild_members(user_id);
CREATE INDEX idx_warnings_user_guild ON warnings(user_id, guild_id, active);
CREATE INDEX idx_mod_actions_guild ON mod_actions(guild_id, created_at);
CREATE INDEX idx_temp_punishments_expires ON temp_punishments(expires_at);
CREATE INDEX idx_reminders_time ON reminders(remind_at, completed);
CREATE INDEX idx_transactions_user ON transactions(user_id, guild_id);
CREATE INDEX idx_command_stats_time ON command_stats(executed_at);
```

---

## Table Documentation

### `users` - Global User Registry

**What it represents:**
- The bot's knowledge of every user across all servers
- Global progression and activity tracking

**When it grows:**
- Every time a new user interacts with the bot in any server
- Typical growth: +100-1000 users per day for active bots

**When it's cleaned:**
- NEVER delete unless user explicitly requests (GDPR)
- Consider soft-delete (mark as deleted) instead of hard-delete

**Who can touch it:**
- User registration system (auto-creates on first interaction)
- GDPR deletion handler (on user request)
- Global XP system (updates XP/level)

**Example queries:**
```sql
-- Get user's global stats
SELECT username, global_xp, global_level, last_seen
FROM users
WHERE user_id = ?;

-- Find top global users
SELECT username, global_xp, global_level
FROM users
ORDER BY global_xp DESC
LIMIT 10;

-- Inactive users (for potential cleanup)
SELECT COUNT(*)
FROM users
WHERE last_seen < datetime('now', '-90 days');
```

---

### `guild_members` - Per-Server User Data

**What it represents:**
- User progression and currency specific to each server
- The link between a user and their activity in a specific community

**When it grows:**
- When a user first interacts in a new server (not when they join)
- Typical growth: 50-500 rows per day per active server

**When it's cleaned:**
- When user leaves the server (optional - consider keeping for return)
- When guild kicks the bot (cascade delete all that guild's data)
- Archives users inactive > 6 months

**Who can touch it:**
- XP system (updates xp, level on messages)
- Economy system (modifies coins)
- Member join/leave events (creates/archives)

**Important relationships:**
```
users.user_id ← guild_members.user_id
                      ↓
              One user = many guild memberships
```

**Example queries:**
```sql
-- Get user's stats in a guild
SELECT u.username, gm.xp, gm.level, gm.coins
FROM guild_members gm
JOIN users u ON gm.user_id = u.user_id
WHERE gm.user_id = ? AND gm.guild_id = ?;

-- Server leaderboard
SELECT u.username, gm.xp, gm.level
FROM guild_members gm
JOIN users u ON gm.user_id = u.user_id
WHERE gm.guild_id = ?
ORDER BY gm.xp DESC
LIMIT 10;

-- Richest users in server
SELECT u.username, gm.coins
FROM guild_members gm
JOIN users u ON gm.user_id = u.user_id
WHERE gm.guild_id = ?
ORDER BY gm.coins DESC
LIMIT 10;
```

---

### `guild_config` - Server Settings

**What it represents:**
- Each server's unique configuration and preferences
- The "personality" of how the bot behaves in that server

**When it grows:**
- One row per server (controlled growth)
- Typical max: Number of servers bot is in

**When it's cleaned:**
- When bot is removed from server (immediate deletion)
- Never grows out of control (1 row = 1 server)

**Who can touch it:**
- Setup commands (initial configuration)
- Admin commands (updates settings)
- Guild leave event (deletes configuration)

**Example queries:**
```sql
-- Get server configuration
SELECT prefix, welcome_channel_id, xp_enabled
FROM guild_config
WHERE guild_id = ?;

-- Update prefix
UPDATE guild_config
SET prefix = ?, updated_at = CURRENT_TIMESTAMP
WHERE guild_id = ?;

-- Create default config for new server
INSERT INTO guild_config (guild_id, prefix)
VALUES (?, '!');
```

---

### `warnings` - User Infractions

**What it represents:**
- Disciplinary records of rule violations
- Progressive punishment system foundation

**When it grows:**
- Every time a moderator issues a warning
- Typical: 5-50 per day in active moderated servers

**When it's cleaned:**
- Warnings expire after configurable period (30-90 days typical)
- Automated cleanup sets `active = FALSE` for expired warnings
- Hard delete after 1 year for GDPR compliance

**Who can touch it:**
- Warn command (creates warnings)
- Cleanup task (expires old warnings)
- Pardon command (deactivates specific warning)

**Retention policy:**
```sql
-- Expire warnings older than 90 days
UPDATE warnings
SET active = FALSE
WHERE created_at < datetime('now', '-90 days')
  AND active = TRUE;

-- Delete warnings older than 1 year (hard cleanup)
DELETE FROM warnings
WHERE created_at < datetime('now', '-365 days');
```

**Example queries:**
```sql
-- Get active warnings for user in guild
SELECT id, reason, created_at, moderator_id
FROM warnings
WHERE user_id = ? AND guild_id = ? AND active = TRUE
ORDER BY created_at DESC;

-- Count warnings per user
SELECT user_id, COUNT(*) as warning_count
FROM warnings
WHERE guild_id = ? AND active = TRUE
GROUP BY user_id
ORDER BY warning_count DESC;
```

---

### `mod_actions` - Complete Moderation Log

**What it represents:**
- Permanent audit trail of all moderation actions
- Legal and accountability record

**When it grows:**
- Every moderation action (kick, ban, mute, warn, etc.)
- Typical: 10-100 per day in active servers
- THIS TABLE GROWS FOREVER (by design)

**When it's cleaned:**
- NEVER (permanent audit log)
- Optional: Archive to cold storage after 1 year
- Keep at least summary stats forever

**Who can touch it:**
- Moderation commands (creates entries)
- NOBODY deletes (append-only table)
- Analytics system (reads for reports)

**Why it never deletes:**
- Legal requirement for accountability
- Appeal investigation requires history
- Pattern detection needs long-term data

**Example queries:**
```sql
-- Get moderation history for user
SELECT action_type, reason, moderator_id, created_at
FROM mod_actions
WHERE target_id = ? AND guild_id = ?
ORDER BY created_at DESC
LIMIT 20;

-- Most active moderators this month
SELECT moderator_id, COUNT(*) as action_count
FROM mod_actions
WHERE guild_id = ?
  AND created_at > datetime('now', '-30 days')
GROUP BY moderator_id
ORDER BY action_count DESC;

-- Action type distribution
SELECT action_type, COUNT(*) as count
FROM mod_actions
WHERE guild_id = ?
  AND created_at > datetime('now', '-30 days')
GROUP BY action_type;
```

---

### `temp_punishments` - Active Temporary Restrictions

**What it represents:**
- Currently active temporary punishments (mutes, temp bans)
- Bot checks this table to enforce punishments

**When it grows:**
- When temporary punishment is issued
- Stays small (only active punishments)

**When it's cleaned:**
- Background task checks every minute for expired punishments
- Removes immediately after punishment expires
- Auto-cleanup is CRITICAL - this table must stay current

**Who can touch it:**
- Mute/tempban commands (creates entries)
- Punishment expiry task (removes expired)
- Unmute/unban commands (removes early)

**Background task (REQUIRED):**
```python
@tasks.loop(minutes=1)
async def check_expired_punishments():
    """Critical task - removes expired punishments."""
    expired = await db.fetch_all("""
        SELECT * FROM temp_punishments
        WHERE expires_at <= CURRENT_TIMESTAMP
    """)
    
    for punishment in expired:
        # Remove the punishment (unmute/unban)
        if punishment['punishment_type'] == 'mute':
            await remove_mute(punishment['user_id'], punishment['guild_id'])
        elif punishment['punishment_type'] == 'ban':
            await remove_ban(punishment['user_id'], punishment['guild_id'])
        
        # Delete from database
        await db.execute(
            "DELETE FROM temp_punishments WHERE id = ?",
            (punishment['id'],)
        )
```

---

### `transactions` - Economy Activity Log

**What it represents:**
- Complete financial history of all users
- Audit trail for economy debugging
- Data for economy balancing

**When it grows:**
- Every economic action (daily rewards, gambling, purchases, transfers)
- High growth rate: 100-10,000 per day depending on activity

**When it's cleaned:**
- Archive transactions older than 90 days to separate table
- Keep aggregated stats forever
- Never delete recent transactions (fraud investigation)

**Who can touch it:**
- Economy commands (creates transactions)
- Aggregation task (reads for stats)
- Admin commands (reads for investigation)

**Example queries:**
```sql
-- User's transaction history
SELECT amount, transaction_type, description, created_at
FROM transactions
WHERE user_id = ? AND guild_id = ?
ORDER BY created_at DESC
LIMIT 20;

-- Daily coin generation
SELECT DATE(created_at) as date, SUM(amount) as total
FROM transactions
WHERE guild_id = ?
  AND amount > 0
  AND created_at > datetime('now', '-30 days')
GROUP BY DATE(created_at);

-- Gambling losses (for balance tuning)
SELECT SUM(amount) as total_loss
FROM transactions
WHERE transaction_type = 'gamble'
  AND amount < 0
  AND created_at > datetime('now', '-7 days');
```

---

## Data Lifecycle

### Creation → Active → Archive → Delete

```
NEW DATA
   ↓
ACTIVE USE (hot storage, indexed, fast queries)
   ↓
AGE > 90 days?
   ↓
ARCHIVE (cold storage, compressed, slow queries OK)
   ↓
AGE > 1 year?
   ↓
AGGREGATE & DELETE (keep summary stats only)
```

### Example: Warning Lifecycle

```
Day 0:  User warned → INSERT INTO warnings
Day 1-89: Warning active → used for automated actions
Day 90: Expires → SET active = FALSE
Day 365: Archive → Move to warnings_archive
Day 730: Delete → Keep only in summary stats
```

---

## Maintenance

### Daily Tasks

```python
@tasks.loop(hours=24)
async def daily_maintenance():
    """Daily database maintenance."""
    
    # 1. Expire old warnings
    await db.execute("""
        UPDATE warnings
        SET active = FALSE
        WHERE created_at < datetime('now', '-90 days')
          AND active = TRUE
    """)
    
    # 2. Archive old transactions
    await db.execute("""
        INSERT INTO transactions_archive
        SELECT * FROM transactions
        WHERE created_at < datetime('now', '-90 days')
    """)
    
    await db.execute("""
        DELETE FROM transactions
        WHERE created_at < datetime('now', '-90 days')
    """)
    
    # 3. Update last_seen for inactive detection
    # (handled by on_message event)
    
    # 4. Vacuum database (SQLite only)
    await db.execute("VACUUM")
    
    logger.info("Daily maintenance completed")
```

### Weekly Tasks

```python
@tasks.loop(hours=168)  # Weekly
async def weekly_maintenance():
    """Weekly database cleanup and optimization."""
    
    # 1. Hard delete very old warnings
    deleted = await db.execute("""
        DELETE FROM warnings
        WHERE created_at < datetime('now', '-365 days')
    """)
    logger.info(f"Deleted {deleted} old warnings")
    
    # 2. Generate analytics snapshots
    await generate_weekly_stats()
    
    # 3. Check for data anomalies
    await check_data_integrity()
    
    # 4. Optimize indexes (PostgreSQL)
    await db.execute("REINDEX DATABASE")
```

---

## Migration Strategy

### Version Control for Schema

```python
# migrations/001_initial_schema.sql
# migrations/002_add_xp_system.sql
# migrations/003_add_economy.sql

class DatabaseMigration:
    """Handle database migrations."""
    
    async def get_current_version(self) -> int:
        """Get current schema version."""
        try:
            result = await db.fetchone("SELECT version FROM schema_version")
            return result['version'] if result else 0
        except:
            return 0
    
    async def migrate_to_latest(self):
        """Run all pending migrations."""
        current = await self.get_current_version()
        migrations = sorted(Path("migrations").glob("*.sql"))
        
        for migration_file in migrations:
            version = int(migration_file.stem.split('_')[0])
            
            if version > current:
                logger.info(f"Running migration {version}: {migration_file.name}")
                
                with open(migration_file) as f:
                    await db.execute_script(f.read())
                
                await db.execute(
                    "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                    (version,)
                )
                
                logger.info(f"Migration {version} completed")
```

---

## Backup and Recovery

### Automated Backups

```python
@tasks.loop(hours=6)  # Every 6 hours
async def backup_database():
    """Create database backup."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/bot_backup_{timestamp}.db"
    
    # SQLite: Simple file copy
    shutil.copy2("bot.db", backup_file)
    
    # Compress
    with zipfile.ZipFile(f"{backup_file}.zip", 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(backup_file)
    
    os.remove(backup_file)  # Remove uncompressed
    
    # Clean old backups (keep 30 days)
    for old_backup in Path("backups").glob("*.zip"):
        if old_backup.stat().st_mtime < time.time() - (30 * 86400):
            old_backup.unlink()
    
    logger.info(f"Backup created: {backup_file}.zip")
```

### PostgreSQL Backup

```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U botuser -d botdb > "backups/backup_$DATE.sql"
gzip "backups/backup_$DATE.sql"

# Delete backups older than 30 days
find backups/ -name "*.sql.gz" -mtime +30 -delete
```

---

## Best Practices Summary

1. **Document the "why" not just the "what"**
   - Explain what data represents in your bot's world

2. **Plan for growth from day one**
   - Index appropriately
   - Consider archiving strategies

3. **Automate cleanup**
   - Data grows forever unless you actively clean it
   - Define retention policies upfront

4. **Never delete audit logs**
   - Moderation actions = permanent record
   - Archive, don't delete

5. **Backup regularly**
   - Automate backups
   - Test recovery procedures

6. **Version your schema**
   - Use migrations for changes
   - Never modify schema manually in production

**Remember:** Your database is the memory of your bot. Treat it with care, document thoroughly, and maintain actively.
