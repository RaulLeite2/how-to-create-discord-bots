# Common discord.py Errors (Human Causes)
This page lists errors and exceptions that frequently appear due to human mistakes during development with `discord.py`, their probable causes, how to identify them, and recommended fixes. Includes handling and logging examples.

---

## How to Read a Traceback
- The *traceback* shows the chain of calls that led to the error; the last line typically indicates the exception and message.
- Read from bottom to top: the final line shows the exception type; the lines above show where in your code it occurred.
- When reporting a bug, copy the complete traceback (including the lines from your code).

---

## Common Errors and Solutions

### 1) `AttributeError`
- What it is: attempt to access an attribute that doesn't exist on an object.
- Typical human cause: typo (e.g., `message_conent` instead of `message_content`), using wrong object attribute, or using a `None` object.
- How to identify: traceback shows `AttributeError: 'X' object has no attribute 'y'`.
- Fix: check the attribute name, ensure the object is not `None` before accessing.

Example:
```python
# Wrong
intents = discord.Intents.default()
intents.message_conent = True  # Typo -> AttributeError

# Correct
intents.message_content = True
```

### 2) `NameError`
- What it is: using a variable that hasn't been defined.
- Typical human cause: forgetting to declare/import, typo in variable/function name.
- How to identify: `NameError: name 'x' is not defined`.
- Fix: declare/import the variable, fix the name.

Example:
```python
# Wrong
await ctx.send(mesage)

# Raises: NameError: name 'mesage' is not defined

# Correct
await ctx.send(message)
```

### 3) `TypeError` / `ValueError`
- `TypeError`: function call with wrong argument type (e.g., passing a `str` where `int` was expected).
- `ValueError`: invalid value for the operation (e.g., `int('abc')`).
- Typical human cause: insufficient parameter validation.
- Fix: validate inputs / use `try/except`.

Example:
```python
try:
    page = int(user_input)
except ValueError:
    await ctx.send("Please provide a valid number.")
```

### 4) `KeyError` / `IndexError`
- Happens when accessing non-existent keys in dictionaries or out-of-range indices in lists.
- Typical human cause: assuming presence of key/index without checking.
- Fix: use `dict.get()` or check `in` before, validate indices.

Example:
```python
# Use get to avoid KeyError
prefix = settings.get('prefix', '!')

# Check index
if len(items) > 0:
    first = items[0]
```

### 5) `ImportError` / `ModuleNotFoundError`
- Happens when a dependency is not installed or module name is incorrect.
- Typical human cause: forgetting to install package, error in `requirements.txt`.
- Fix: `pip install <package>` and keep `requirements.txt` updated.

### 6) `discord.Forbidden`, `discord.NotFound`, `discord.HTTPException`
- Discord API errors:
  - `Forbidden`: bot doesn't have permission (e.g., trying to ban without permission).
  - `NotFound`: resource not found (message/user deleted).
  - `HTTPException`: HTTP request failed (rate limit, invalid content).
- Typical human cause: not configuring correct permissions, operating on invalid objects.
- Fix: verify permissions, handle exceptions and inform the user.

Example:
```python
try:
    await member.ban(reason=reason)
except discord.Forbidden:
    await ctx.send("I don't have permission to ban this member.")
except discord.HTTPException as e:
    await ctx.send(f"Request failed: {e}")
```

### 7) `commands.CommandNotFound`, `commands.MissingRequiredArgument`, `commands.MissingPermissions`, `commands.CheckFailure`
- Common errors when using the `discord.ext.commands` command system.
- Typical human cause: user typed invalid command, missing required argument, or user/bot lacks permissions.
- Fix: capture in `on_command_error` and send friendly messages.

Global handling example:
```python
from discord.ext import commands

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return  # optional: ignore
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: {error.param.name}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("I don't have the necessary permissions for this.")
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("You didn't pass a check required to use this command.")
    else:
        # Complete log for developer
        logger.exception("Unhandled command error")
        await ctx.send("An internal error occurred. The developer has been notified.")
```

### 8) `asyncio.TimeoutError` / Lost Connections
- Happens when async calls take too long or external services become unavailable.
- Typical human cause: not handling timeouts in external requests or database.
- Fix: use explicit timeouts and retries.

Example with timeout:
```python
import asyncio

try:
    await asyncio.wait_for(some_coro(), timeout=10)
except asyncio.TimeoutError:
    await ctx.send("Request timed out. Please try again later.")
```

### 9) `RuntimeError` / `Event loop is closed`
- Can occur when trying to run `asyncio.run()` while a loop is already running (e.g., in bot contexts).
- Typical human cause: using async execution API incorrectly when integrating with frameworks.
- Fix: use `asyncio.run()` only at the entry point; inside the bot, use `await` and `bot.loop`.

### 10) Invalid Token / `LoginFailure`
- Message: `discord.errors.LoginFailure: Improper token has been passed.`
- Typical human cause: wrong token, exposed and reset token, environment variables not loaded.
- Fix: check `.env`, `config`, and don't commit tokens. Test with `print(TOKEN is None)`.

---

## Best Practices to Avoid Human Errors
1. Enable and validate correct `intents` (e.g., `intents.message_content = True`) and verify in Discord portal.
2. Use a `.env` file and don't commit tokens.
3. Test commands locally before deploying.
4. Write input validation (type hints and checks).
5. Use `typing` and linters (mypy, flake8) to catch name and type errors.
6. Use unit tests for critical functions.
7. Use structured logs and catch unhandled exceptions.

---

## Recommended Logging
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[logging.FileHandler('bot.log'), logging.StreamHandler()]
)
logger = logging.getLogger('bot')

# Usage example
try:
    # error-prone operation
    pass
except Exception:
    logger.exception("Unexpected error while executing operation")
```

---

## Automatic Error Reporting
- Consider integrating Sentry to automatically collect tracebacks and metrics.
- For Sentry: `pip install sentry-sdk`

Minimal example:
```python
import sentry_sdk
sentry_sdk.init(dsn="https://<key>@sentry.io/<project_id>")
```

---

## Quick Checklist When Seeing an Error
- Copy the complete traceback.
- Reproduce locally with the same inputs.
- Verify environment variables are correct.
- Check bot permissions on the server.
- Confirm Python and dependency versions (`pip freeze`).

---

## Additional Resources

- [discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord API Error Codes](https://discord.com/developers/docs/topics/opcodes-and-status-codes)
- [Python Exception Hierarchy](https://docs.python.org/3/library/exceptions.html)
- [Sentry Documentation](https://docs.sentry.io/)

