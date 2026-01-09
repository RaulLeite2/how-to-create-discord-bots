# Architecture Documentation
**System design, connections, and decision rationale**

This document explains how all components of the bot connect, their responsibilities, and why certain architectural decisions were made. This is the backbone of the project.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Design Decisions](#design-decisions)
5. [Scalability Strategy](#scalability-strategy)
6. [Security Model](#security-model)
7. [Future Considerations](#future-considerations)

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Discord Platform                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Server A  │  │   Server B  │  │   Server C  │         │
│  │   (Users)   │  │   (Users)   │  │   (Users)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└──────────────────────────┬──────────────────────────────────┘
                           │ WebSocket / REST API
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                       Discord Bot                            │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Main Process                         │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │ │
│  │  │ Event Loop   │  │ Command      │  │ Task        │  │ │
│  │  │ (asyncio)    │  │ Processor    │  │ Manager     │  │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Cog System                           │ │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────┐       │ │
│  │  │ Moderation │ │  Economy   │ │     Fun      │  ...  │ │
│  │  │    Cog     │ │    Cog     │ │     Cog      │       │ │
│  │  └────────────┘ └────────────┘ └──────────────┘       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   Utilities Layer                       │ │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────┐       │ │
│  │  │   Checks   │ │ Converters │ │    Embeds    │       │ │
│  │  └────────────┘ └────────────┘ └──────────────┘       │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   Data Layer                            │ │
│  │  ┌────────────────────────────────────────────────────┐│ │
│  │  │          Database Manager (Connection Pool)        ││ │
│  │  └────────────────────────────────────────────────────┘│ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬───────────────────────────────────┘
                            │
                            │
┌───────────────────────────▼───────────────────────────────────┐
│                     Database Server                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │    Users     │  │   Guilds     │  │  Mod Actions │  ...   │
│  │    Table     │  │    Table     │  │    Table     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└───────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Main Process (`main.py`)

**Responsibilities:**
- Initialize bot instance
- Load configuration
- Setup database connection
- Load all cogs
- Handle bot lifecycle (startup, shutdown)
- Coordinate background tasks

**Why this design:**
- Single entry point makes deployment simple
- Centralized initialization catches configuration errors early
- Clean shutdown ensures data integrity

**Code structure:**
```python
# main.py
import asyncio
import discord
from discord.ext import commands

# Initialize bot
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=discord.Intents.all(),
    help_command=None  # Custom help command
)

async def main():
    async with bot:
        # Setup phase
        await setup_database()
        await load_cogs()
        await setup_logging()
        
        # Run bot
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
```

---

### 2. Cog System

**Responsibilities:**
- Organize commands by feature
- Isolate functionality
- Enable hot-reloading during development
- Manage feature-specific state

**Why cogs:**
- **Modularity** - Each feature is self-contained
- **Maintainability** - Easy to find and modify code
- **Scalability** - Can disable features per-server
- **Development** - Reload cogs without restarting bot

**Cog structure:**
```
cogs/
├── __init__.py
├── moderation.py      # Kick, ban, mute, warn
├── economy.py         # Coins, shop, gambling
├── leveling.py        # XP and levels
├── fun.py             # Games and entertainment
├── utility.py         # Info commands
└── admin.py           # Bot management
```

**Communication between cogs:**
```python
# ❌ Don't do this - tight coupling
class EconomyCog:
    async def add_coins(self, user_id, amount):
        # Direct call to another cog
        leveling_cog = self.bot.get_cog("LevelingCog")
        await leveling_cog.add_xp(user_id, amount * 10)

# ✅ Do this - event-based loose coupling
class EconomyCog:
    async def add_coins(self, user_id, amount):
        # Dispatch event that other cogs can listen to
        self.bot.dispatch('coins_earned', user_id, amount)

class LevelingCog:
    @commands.Cog.listener()
    async def on_coins_earned(self, user_id, amount):
        # React to event
        await self.add_xp(user_id, amount * 10)
```

---

### 3. Database Layer

**Responsibilities:**
- Manage database connections
- Execute queries safely
- Handle transactions
- Connection pooling

**Why a separate layer:**
- **Security** - Centralized query sanitization
- **Performance** - Connection pooling
- **Testability** - Easy to mock
- **Maintainability** - Database logic in one place

**Implementation:**
```python
# database/manager.py
class DatabaseManager:
    """Centralized database access."""
    
    def __init__(self, connection_string: str):
        self.pool = None
        self.connection_string = connection_string
    
    async def connect(self):
        """Create connection pool."""
        self.pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=20
        )
    
    async def execute(self, query: str, *args):
        """Execute query safely."""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetchone(self, query: str, *args):
        """Fetch single row."""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
    
    async def fetchall(self, query: str, *args):
        """Fetch all rows."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)
    
    @contextlib.asynccontextmanager
    async def transaction(self):
        """Transaction context manager."""
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                yield conn
```

**Usage in cogs:**
```python
# In cog
async def transfer_coins(self, from_user, to_user, amount):
    async with self.bot.db.transaction() as conn:
        # Both queries succeed or both fail
        await conn.execute(
            "UPDATE guild_members SET coins = coins - $1 WHERE user_id = $2",
            amount, from_user
        )
        await conn.execute(
            "UPDATE guild_members SET coins = coins + $1 WHERE user_id = $2",
            amount, to_user
        )
```

---

### 4. Utilities Layer

**Responsibilities:**
- Reusable helper functions
- Custom checks and converters
- Embed builders
- Common validations

**Why separate utilities:**
- **DRY** - Don't repeat code across cogs
- **Consistency** - Same look and behavior everywhere
- **Testing** - Easy to unit test
- **Reusability** - Use in multiple cogs

**Structure:**
```
utils/
├── __init__.py
├── checks.py          # Permission checks
├── converters.py      # Argument converters
├── embeds.py          # Embed templates
├── time.py            # Time parsing and formatting
├── pagination.py      # Paginated embeds
└── formatting.py      # Text formatting
```

---

## Data Flow

### Command Execution Flow

```
1. User sends message
        ↓
2. Discord sends to bot via WebSocket
        ↓
3. discord.py fires on_message event
        ↓
4. Command processor checks for prefix
        ↓
5. Command found in cog registry
        ↓
6. Permission checks run
        ↓
7. Argument converters run
        ↓
8. Command function executes
        ↓
9. Database queries (if needed)
        ↓
10. Response sent to Discord
        ↓
11. Discord delivers to user
        ↓
12. on_command_completion event fires
```

### Event Flow

```
Discord Event
     ↓
discord.py library
     ↓
Event dispatcher
     ├─→ Bot-level listeners
     ├─→ Cog listeners (in load order)
     └─→ Custom event handlers
```

---

## Design Decisions

### Decision 1: Monolithic vs Microservices

**Choice:** Monolithic (single process)

**Why:**
- Discord bots have state (guild cache, connection)
- Inter-process communication adds complexity
- Most bots don't need microservice scale
- Easier deployment and debugging

**When to reconsider:**
- Bot serves >10,000 servers
- Need independent scaling of features
- Multiple teams working on different features

---

### Decision 2: SQL vs NoSQL Database

**Choice:** SQL (PostgreSQL/SQLite)

**Why:**
- Relational data (users, guilds, permissions)
- ACID transactions needed (economy, moderation)
- Complex queries required (leaderboards, analytics)
- Mature ecosystem

**When NoSQL would be better:**
- Heavily nested data structures
- Extreme write throughput
- Flexible schema requirements

---

### Decision 3: Cog Architecture

**Choice:** Plugin-based cogs

**Why:**
- Logical feature separation
- Hot-reload during development
- Easy to enable/disable features
- Clear code organization

**Alternative considered:**
- Flat command structure (rejected - becomes unmaintainable)

---

### Decision 4: Async vs Sync

**Choice:** Fully async (asyncio)

**Why:**
- Discord API is async by nature
- Handle multiple servers concurrently
- Don't block on I/O operations
- Better resource utilization

**Challenges:**
- Steeper learning curve
- Must use async libraries
- Debugging is harder

---

### Decision 5: Configuration Management

**Choice:** Environment variables + database

**Why:**
- Environment variables for secrets (tokens, API keys)
- Database for per-guild configuration
- Clear separation of concerns

**Structure:**
```python
# Secrets from environment
TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Per-guild config from database
guild_config = await db.fetchone(
    "SELECT * FROM guild_config WHERE guild_id = ?",
    guild_id
)
prefix = guild_config['prefix']
```

---

## Scalability Strategy

### Current Scale: 1-1000 Servers

**Architecture:**
- Single process
- SQLite or small PostgreSQL
- Simple deployment

**Bottlenecks:**
- Single-process limit
- Database connection limit
- Memory for guild cache

---

### Medium Scale: 1,000-10,000 Servers

**Required changes:**
- Switch to PostgreSQL with connection pooling
- Implement caching (Redis)
- Horizontal scaling with sharding
- Load balancer

**Architecture:**
```
                    ┌─────────────┐
                    │ Load        │
                    │ Balancer    │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌─────────┐      ┌─────────┐     ┌─────────┐
    │  Shard  │      │  Shard  │     │  Shard  │
    │    0    │      │    1    │     │    2    │
    │ (0-999) │      │(1K-1.9K)│     │(2K-2.9K)│
    └────┬────┘      └────┬────┘     └────┬────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                    ┌─────▼─────┐
                    │ Shared    │
                    │ PostgreSQL│
                    └───────────┘
```

---

### Large Scale: 10,000+ Servers

**Required changes:**
- Multiple shards per process
- Dedicated cache cluster
- Message queue for inter-shard communication
- Separate API server

**Architecture:**
```
Users → Discord → Gateway → Shard Manager → Shards
                                   │
                                   ├─→ Redis (Cache)
                                   ├─→ RabbitMQ (Messages)
                                   ├─→ PostgreSQL (Data)
                                   └─→ API Server
```

---

## Security Model

### Threat Model

**Threats we protect against:**
1. SQL injection
2. Command injection
3. Privilege escalation
4. Rate limit abuse
5. Data leaks

### Security Layers

**Layer 1: Input Validation**
```python
# Validate ALL user input
@bot.command()
async def transfer(ctx, amount: int, member: discord.Member):
    # Type converters provide first layer
    # Additional validation
    if amount <= 0:
        raise commands.BadArgument("Amount must be positive")
    if amount > 1000000:
        raise commands.BadArgument("Amount too large")
```

**Layer 2: Permission Checks**
```python
# Always check permissions
@bot.command()
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    # Both user and bot permissions checked
    pass
```

**Layer 3: Rate Limiting**
```python
# Prevent abuse
@bot.command()
@commands.cooldown(1, 60, commands.BucketType.user)
async def daily(ctx):
    # 1 use per 60 seconds per user
    pass
```

**Layer 4: Database Security**
```python
# Parameterized queries always
await db.execute(
    "SELECT * FROM users WHERE id = ?",
    (user_id,)  # Safe from injection
)

# Never this:
await db.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

**Layer 5: Secrets Management**
```python
# Never in code
TOKEN = os.getenv("DISCORD_TOKEN")

# Never log secrets
logger.info(f"Starting bot...")  # Good
logger.info(f"Token: {TOKEN}")   # BAD!!!
```

---

## Future Considerations

### Potential Enhancements

**1. Web Dashboard**
- User-friendly configuration
- Real-time statistics
- Moderation log viewer

**2. API Layer**
- RESTful API for external integrations
- Webhooks for events
- OAuth2 for authentication

**3. Machine Learning**
- Auto-moderation (spam detection)
- Content filtering
- User behavior analysis

**4. Multi-Language Support**
- i18n for commands
- Per-guild language settings
- Crowdsourced translations

**5. Plugin System**
- Community-developed extensions
- Sandboxed execution
- Plugin marketplace

---

## Deployment Architecture

### Development Environment

```
Developer Machine
├─ VS Code
├─ Python 3.11+
├─ SQLite database
└─ Local Discord bot (test server)
```

### Staging Environment

```
Staging Server
├─ Docker container
├─ PostgreSQL database
├─ Full bot features
└─ Test guilds only
```

### Production Environment

```
Production Server
├─ Docker container (with restart policy)
├─ PostgreSQL (with replication)
├─ Redis (caching)
├─ Monitoring (Prometheus/Grafana)
├─ Log aggregation (ELK stack)
└─ Automated backups
```

---

## Monitoring and Observability

### Metrics to Track

**Bot Health:**
- Uptime percentage
- WebSocket latency
- Command response time
- Error rate

**Usage:**
- Commands per minute
- Active users
- Active guilds
- Most used commands

**Resources:**
- Memory usage
- CPU usage
- Database connections
- Cache hit rate

### Logging Strategy

```python
# Structured logging
logger.info("Command executed", extra={
    "command": ctx.command.name,
    "user_id": ctx.author.id,
    "guild_id": ctx.guild.id,
    "latency_ms": latency
})
```

---

## Conclusion

This architecture is designed for:
- ✅ Maintainability through clear separation
- ✅ Scalability through modular design
- ✅ Security through layered defenses
- ✅ Reliability through proper error handling
- ✅ Observability through comprehensive logging

**Remember:** Architecture evolves. Revisit this document as the bot grows and requirements change.

---

## Further Reading

- [STYLEGUIDE.md](STYLEGUIDE.md) - Code standards
- [DATABASE.md](DATABASE.md) - Data architecture
- [LIFECYCLE.md](LIFECYCLE.md) - Request flow
- [PERMISSIONS.md](PERMISSIONS.md) - Security model
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute
