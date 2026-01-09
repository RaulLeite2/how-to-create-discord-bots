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

@bot.command(name='greet')
async def greet(ctx, name):
    """Greets a user by name"""
    await ctx.send(f'Hello, {name}! 👋')

@bot.command(name='add')
async def add(ctx, num1: int, num2: int):
    """Adds two numbers"""
    result = num1 + num2
    await ctx.send(f'{num1} + {num2} = {result}')

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

@bot.command(name='serverinfo')
async def serverinfo(ctx):
    """Displays server information"""
    guild = ctx.guild
    embed = discord.Embed(
        title=f"{guild.name}",
        description=f"Server information for {guild.name}",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
    embed.add_field(name="Server ID", value=guild.id, inline=True)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Created At", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    await ctx.send(embed=embed)

# Run the bot
if __name__ == '__main__':
    if TOKEN is None:
        print("Error: DISCORD_TOKEN not found in environment variables.")
        print("Please create a .env file with your bot token.")
    else:
        bot.run(TOKEN)
