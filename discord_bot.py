import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import datetime
import json
import os
from typing import Optional
import time

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Remove default help command and add custom one
bot.remove_command('help')

# Data storage files
WARNINGS_FILE = 'warnings.json'
LEVELS_FILE = 'levels.json'

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

# ============================================================================
# EVENT HANDLERS
# ============================================================================

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print(f'Connected to {len(bot.guilds)} servers')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands')
    except Exception as e:
        print(f'Failed to sync slash commands: {e}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Level system
    await handle_level_system(message)
    
    # Auto-moderation (basic profanity filter)
    await check_profanity(message)
    
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    # Welcome new members
    welcome_channel = None
    for channel in member.guild.text_channels:
        if 'welcome' in channel.name.lower() or 'general' in channel.name.lower():
            welcome_channel = channel
            break
    
    if welcome_channel:
        embed = discord.Embed(
            title="🎉 Welcome!",
            description=f"Welcome to **{member.guild.name}**, {member.mention}!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Member Count", value=f"{member.guild.member_count}")
        embed.set_footer(text="Feel free to introduce yourself!")
        await welcome_channel.send(embed=embed)

# ============================================================================
# LEVEL SYSTEM
# ============================================================================

async def handle_level_system(message):
    if not message.guild:
        return
    
    levels = load_json(LEVELS_FILE)
    guild_id = str(message.guild.id)
    user_id = str(message.author.id)
    
    if guild_id not in levels:
        levels[guild_id] = {}
    
    if user_id not in levels[guild_id]:
        levels[guild_id][user_id] = {'xp': 0, 'level': 1, 'messages': 0}
    
    # Add XP (10 per message)
    levels[guild_id][user_id]['xp'] += 10
    levels[guild_id][user_id]['messages'] += 1
    
    # Calculate level (every 100 XP = level up)
    xp = levels[guild_id][user_id]['xp']
    level = (xp // 100) + 1
    
    if level > levels[guild_id][user_id]['level']:
        levels[guild_id][user_id]['level'] = level
        # Send level up message
        channel = message.channel
        embed = discord.Embed(
            title="🎊 Level Up!",
            description=f"{message.author.mention} just reached **Level {level}**!",
            color=discord.Color.gold()
        )
        await channel.send(embed=embed)
    
    save_json(LEVELS_FILE, levels)

# ============================================================================
# AUTO-MODERATION
# ============================================================================

PROFANITY_LIST = ['badword1', 'badword2']  # Add your own list

async def check_profanity(message):
    if message.author.guild_permissions.manage_messages:
        return
    
    content_lower = message.content.lower()
    for word in PROFANITY_LIST:
        if word in content_lower:
            await message.delete()
            embed = discord.Embed(
                title="⚠️ Language Warning",
                description=f"{message.author.mention}, please keep the language appropriate.",
                color=discord.Color.orange()
            )
            msg = await message.channel.send(embed=embed, delete_after=5)
            break

# ============================================================================
# SLASH COMMANDS
# ============================================================================

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Bot latency: **{latency}ms**",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="userinfo", description="Get information about a user")
async def userinfo(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    if member is None:
        member = interaction.user
    
    embed = discord.Embed(
        title=f"👤 User Info - {member.display_name}",
        color=member.color
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="Username", value=member.name, inline=True)
    embed.add_field(name="Discriminator", value=member.discriminator, inline=True)
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Roles", value=f"{len(member.roles)} roles", inline=True)
    embed.add_field(name="Top Role", value=member.top_role.name, inline=True)
    embed.set_footer(text=f"Requested by {interaction.user}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="serverinfo", description="Get information about the server")
async def serverinfo(interaction: discord.Interaction):
    guild = interaction.guild
    
    embed = discord.Embed(
        title=f"🏰 Server Info - {guild.name}",
        color=discord.Color.green()
    )
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Created", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Text Channels", value=len(guild.text_channels), inline=True)
    embed.add_field(name="Voice Channels", value=len(guild.voice_channels), inline=True)
    embed.add_field(name="Categories", value=len(guild.categories), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    embed.add_field(name="Emojis", value=len(guild.emojis), inline=True)
    embed.set_footer(text=f"Server ID: {guild.id}")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="avatar", description="Get a user's avatar")
async def avatar(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    if member is None:
        member = interaction.user
    
    embed = discord.Embed(
        title=f"🖼️ {member.display_name}'s Avatar",
        color=discord.Color.blue()
    )
    embed.set_image(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="roll", description="Roll a dice")
async def roll(interaction: discord.Interaction, sides: int = 6):
    if sides < 2 or sides > 1000:
        embed = discord.Embed(
            title="❌ Invalid Input",
            description="Please choose between 2 and 1000 sides.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    result = random.randint(1, sides)
    embed = discord.Embed(
        title="🎲 Dice Roll",
        description=f"You rolled a **{result}** on a {sides}-sided die!",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="flip", description="Flip a coin")
async def flip(interaction: discord.Interaction):
    result = random.choice(['Heads', 'Tails'])
    embed = discord.Embed(
        title="🪙 Coin Flip",
        description=f"The coin landed on **{result}**!",
        color=discord.Color.gold()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="8ball", description="Ask the magic 8-ball a question")
async def eightball(interaction: discord.Interaction, question: str):
    responses = [
        "Yes, definitely!",
        "Without a doubt.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    
    embed = discord.Embed(
        title="🔮 Magic 8-Ball",
        description=f"**Question:** {question}\n\n**Answer:** {random.choice(responses)}",
        color=discord.Color.dark_purple()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.describe(text="The text to say")
async def say(interaction: discord.Interaction, text: str):
    if interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(text)
    else:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need `Manage Messages` permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="kick", description="Kick a member from the server")
@app_commands.describe(member="The member to kick", reason="Reason for kicking")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.kick_members:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need `Kick Members` permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if member.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Cannot Kick",
            description="Cannot kick an administrator!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"{member.mention} has been kicked from the server.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Moderator", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to kick member: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="ban", description="Ban a member from the server")
@app_commands.describe(member="The member to ban", reason="Reason for banning")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
    if not interaction.user.guild_permissions.ban_members:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need `Ban Members` permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    if member.guild_permissions.administrator:
        embed = discord.Embed(
            title="❌ Cannot Ban",
            description="Cannot ban an administrator!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    try:
        await member.ban(reason=reason, delete_message_days=1)
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{member.mention} has been banned from the server.",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason)
        embed.add_field(name="Moderator", value=interaction.user.mention)
        await interaction.response.send_message(embed=embed)
    except Exception as e:
        embed = discord.Embed(
            title="❌ Error",
            description=f"Failed to ban member: {str(e)}",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="warn", description="Warn a member")
@app_commands.describe(member="The member to warn", reason="Reason for warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not interaction.user.guild_permissions.moderate_members:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need `Moderate Members` permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    warnings = load_json(WARNINGS_FILE)
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    if guild_id not in warnings:
        warnings[guild_id] = {}
    
    if user_id not in warnings[guild_id]:
        warnings[guild_id][user_id] = []
    
    warning_data = {
        'moderator': str(interaction.user.id),
        'reason': reason,
        'timestamp': datetime.datetime.now().isoformat()
    }
    
    warnings[guild_id][user_id].append(warning_data)
    save_json(WARNINGS_FILE, warnings)
    
    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=f"{member.mention} has been warned.",
        color=discord.Color.orange()
    )
    embed.add_field(name="Reason", value=reason)
    embed.add_field(name="Total Warnings", value=len(warnings[guild_id][user_id]))
    embed.add_field(name="Moderator", value=interaction.user.mention)
    
    try:
        await member.send(f"You have been warned in **{interaction.guild.name}**.\nReason: {reason}")
    except:
        pass
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="warnings", description="View warnings for a member")
async def warnings(interaction: discord.Interaction, member: discord.Member):
    warnings = load_json(WARNINGS_FILE)
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    if guild_id not in warnings or user_id not in warnings[guild_id] or len(warnings[guild_id][user_id]) == 0:
        embed = discord.Embed(
            title="✅ No Warnings",
            description=f"{member.mention} has no warnings.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    embed = discord.Embed(
        title="⚠️ Warnings for " + member.display_name,
        color=discord.Color.orange()
    )
    
    for i, warning in enumerate(warnings[guild_id][user_id], 1):
        mod_id = warning['moderator']
        try:
            mod = await bot.fetch_user(int(mod_id))
            mod_name = mod.name
        except:
            mod_name = "Unknown"
        
        timestamp = warning['timestamp'][:10]
        reason = warning['reason']
        embed.add_field(
            name=f"Warning #{i}",
            value=f"**By:** {mod_name}\n**Date:** {timestamp}\n**Reason:** {reason}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="clearwarnings", description="Clear all warnings for a member")
async def clearwarnings(interaction: discord.Interaction, member: discord.Member):
    if not interaction.user.guild_permissions.moderate_members:
        embed = discord.Embed(
            title="❌ Permission Denied",
            description="You need `Moderate Members` permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    
    warnings = load_json(WARNINGS_FILE)
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    if guild_id in warnings and user_id in warnings[guild_id]:
        count = len(warnings[guild_id][user_id])
        del warnings[guild_id][user_id]
        save_json(WARNINGS_FILE, warnings)
        
        embed = discord.Embed(
            title="✅ Warnings Cleared",
            description=f"Cleared **{count}** warnings for {member.mention}.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(
            title="ℹ️ No Warnings",
            description=f"{member.mention} has no warnings to clear.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

@bot.tree.command(name="level", description="Check your level or another user's level")
async def level(interaction: discord.Interaction, member: Optional[discord.Member] = None):
    if member is None:
        member = interaction.user
    
    levels = load_json(LEVELS_FILE)
    guild_id = str(interaction.guild.id)
    user_id = str(member.id)
    
    if guild_id not in levels or user_id not in levels[guild_id]:
        embed = discord.Embed(
            title="📊 Level Info",
            description=f"{member.mention} hasn't earned any XP yet.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    user_data = levels[guild_id][user_id]
    xp = user_data['xp']
    level_num = user_data['level']
    messages = user_data['messages']
    xp_to_next = (level_num * 100) - xp
    
    embed = discord.Embed(
        title="📊 Level Info",
        description=f"{member.mention} is **Level {level_num}**",
        color=discord.Color.gold()
    )
    embed.add_field(name="XP", value=f"{xp} / {level_num * 100}", inline=True)
    embed.add_field(name="Messages", value=messages, inline=True)
    embed.add_field(name="XP to Next Level", value=max(0, xp_to_next), inline=True)
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="leaderboard", description="View the server's level leaderboard")
async def leaderboard(interaction: discord.Interaction):
    levels = load_json(LEVELS_FILE)
    guild_id = str(interaction.guild.id)
    
    if guild_id not in levels or len(levels[guild_id]) == 0:
        embed = discord.Embed(
            title="📊 Leaderboard",
            description="No users have earned XP yet.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    # Sort by XP
    sorted_users = sorted(levels[guild_id].items(), key=lambda x: x[1]['xp'], reverse=True)[:10]
    
    embed = discord.Embed(
        title="🏆 Server Leaderboard",
        description="Top 10 users by level",
        color=discord.Color.gold()
    )
    
    for i, (user_id, data) in enumerate(sorted_users, 1):
        try:
            member = await interaction.guild.fetch_member(int(user_id))
            name = member.display_name
        except:
            name = "Unknown User"
        
        embed.add_field(
            name=f"#{i} - {name}",
            value=f"Level {data['level']} | {data['xp']} XP",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="help", description="Show help information")
async def help_command(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 Bot Help Menu",
        description="Welcome! Here are all available commands:",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📋 General Commands",
        value="`/ping` - Check bot latency\n`/userinfo` - Get user information\n`/serverinfo` - Get server information\n`/avatar` - Get user avatar\n`/help` - Show this menu",
        inline=False
    )
    
    embed.add_field(
        name="🎮 Fun Commands",
        value="`/roll` - Roll a dice\n`/flip` - Flip a coin\n`/8ball` - Ask the magic 8-ball\n`/say` - Make the bot say something",
        inline=False
    )
    
    embed.add_field(
        name="🎲 Mini Games",
        value="`/guess` - Guess the number game\n`/trivia` - Answer trivia questions\n`/rps` - Rock Paper Scissors\n`/tictactoe` - Play Tic-Tac-Toe\n`/wordle` - Daily word puzzle\n`/hangman` - Classic hangman game\n`/quiz` - Quick quiz challenge\n`/memory` - Memory matching game",
        inline=False
    )
    
    embed.add_field(
        name="🛡️ Moderation Commands",
        value="`/kick` - Kick a member\n`/ban` - Ban a member\n`/warn` - Warn a member\n`/warnings` - View warnings\n`/clearwarnings` - Clear warnings",
        inline=False
    )
    
    embed.add_field(
        name="📈 Level System",
        value="`/level` - Check your level\n`/leaderboard` - View leaderboard\n*Earn XP by sending messages!*",
        inline=False
    )
    
    embed.set_footer(text=f"Requested by {interaction.user}")
    await interaction.response.send_message(embed=embed)

# ============================================================================
# MINI GAMES
# ============================================================================

# Game state storage
GAMES_FILE = 'games.json'

def load_games():
    return load_json(GAMES_FILE)

def save_games(data):
    save_json(GAMES_FILE, data)

@bot.tree.command(name="guess", description="Guess the number between 1 and 100")
async def guess(interaction: discord.Interaction):
    number = random.randint(1, 100)
    attempts = 0
    max_attempts = 7
    
    games = load_games()
    games[str(interaction.user.id)] = {'game': 'guess', 'number': number, 'attempts': 0, 'max': max_attempts}
    save_games(games)
    
    embed = discord.Embed(
        title="🎯 Guess the Number",
        description=f"I'm thinking of a number between **1 and 100**.\nYou have **{max_attempts}** attempts!",
        color=discord.Color.purple()
    )
    embed.set_footer(text="Use /guessnumber to make your guess")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="guessnumber", description="Submit your guess")
async def guessnumber(interaction: discord.Interaction, number: int):
    user_id = str(interaction.user.id)
    games = load_games()
    
    if user_id not in games or games[user_id].get('game') != 'guess':
        embed = discord.Embed(
            title="❌ No Active Game",
            description="Start a new game with `/guess` first!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    game = games[user_id]
    game['attempts'] += 1
    remaining = game['max'] - game['attempts']
    
    if number == game['number']:
        embed = discord.Embed(
            title="🎉 Correct!",
            description=f"You guessed it in **{game['attempts']}** attempts!\nThe number was **{number}**!",
            color=discord.Color.green()
        )
        del games[user_id]
        save_games(games)
    elif number < game['number']:
        embed = discord.Embed(
            title="📈 Too Low!",
            description=f"Try higher! You have **{remaining}** attempts left.",
            color=discord.Color.orange()
        )
        save_games(games)
    else:
        embed = discord.Embed(
            title="📉 Too High!",
            description=f"Try lower! You have **{remaining}** attempts left.",
            color=discord.Color.orange()
        )
        save_games(games)
    
    if remaining <= 0 and number != game['number']:
        embed = discord.Embed(
            title="😔 Game Over",
            description=f"You ran out of attempts!\nThe number was **{game['number']}**",
            color=discord.Color.red()
        )
        del games[user_id]
        save_games(games)
    
    await interaction.response.send_message(embed=embed)

TRIVIA_QUESTIONS = [
    {"q": "What is the capital of France?", "a": ["paris"], "difficulty": "easy"},
    {"q": "Which planet is known as the Red Planet?", "a": ["mars"], "difficulty": "easy"},
    {"q": "What is the largest ocean on Earth?", "a": ["pacific", "pacific ocean"], "difficulty": "medium"},
    {"q": "Who wrote 'Romeo and Juliet'?", "a": ["shakespeare", "william shakespeare"], "difficulty": "medium"},
    {"q": "What is the chemical symbol for gold?", "a": ["au"], "difficulty": "hard"},
    {"q": "In what year did World War II end?", "a": ["1945"], "difficulty": "medium"},
    {"q": "What is the smallest prime number?", "a": ["2"], "difficulty": "easy"},
    {"q": "Which country invented pizza?", "a": ["italy"], "difficulty": "easy"},
    {"q": "What is the speed of light (approximate)?", "a": ["300000", "300000 km/s", "3x10^8"], "difficulty": "hard"},
    {"q": "Who painted the Mona Lisa?", "a": ["da vinci", "leonardo da vinci"], "difficulty": "medium"},
]

@bot.tree.command(name="trivia", description="Answer a trivia question")
async def trivia(interaction: discord.Interaction, difficulty: Optional[str] = None):
    if difficulty:
        filtered = [q for q in TRIVIA_QUESTIONS if q['difficulty'] == difficulty.lower()]
        if filtered:
            question = random.choice(filtered)
        else:
            question = random.choice(TRIVIA_QUESTIONS)
    else:
        question = random.choice(TRIVIA_QUESTIONS)
    
    games = load_games()
    games[f"trivia_{interaction.channel.id}"] = {'answer': question['a'], 'question': question['q']}
    save_games(games)
    
    embed = discord.Embed(
        title="🧠 Trivia Time!",
        description=f"**{question['q']}**\n\nDifficulty: {question['difficulty'].title()}",
        color=discord.Color.blue()
    )
    embed.set_footer(text="Type your answer in the chat!")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="rps", description="Play Rock Paper Scissors")
async def rps(interaction: discord.Interaction, choice: str):
    choices = ['rock', 'paper', 'scissors']
    choice_lower = choice.lower()
    
    if choice_lower not in choices:
        embed = discord.Embed(
            title="❌ Invalid Choice",
            description="Please choose: rock, paper, or scissors",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    bot_choice = random.choice(choices)
    
    emojis = {'rock': '🪨', 'paper': '📄', 'scissors': '✂️'}
    
    if choice_lower == bot_choice:
        result = "It's a tie!"
        color = discord.Color.orange()
    elif (choice_lower == 'rock' and bot_choice == 'scissors') or \
         (choice_lower == 'paper' and bot_choice == 'rock') or \
         (choice_lower == 'scissors' and bot_choice == 'paper'):
        result = "You win! 🎉"
        color = discord.Color.green()
    else:
        result = "Bot wins! 🤖"
        color = discord.Color.red()
    
    embed = discord.Embed(
        title="🎮 Rock Paper Scissors",
        description=f"**You:** {emojis[choice_lower]} {choice_lower.title()}\n**Bot:** {emojis[bot_choice]} {bot_choice.title()}\n\n{result}",
        color=color
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="tictactoe", description="Start a Tic-Tac-Toe game")
async def tictactoe(interaction: discord.Interaction, opponent: Optional[discord.Member] = None):
    if opponent is None:
        opponent = bot.user
    
    board = ['⬜'] * 9
    games = load_games()
    games[f"ttt_{interaction.channel.id}"] = {
        'board': board,
        'player1': str(interaction.user.id),
        'player2': str(opponent.id) if opponent != bot.user else 'bot',
        'current': str(interaction.user.id),
        'p1_symbol': '❌',
        'p2_symbol': '⭕'
    }
    save_games(games)
    
    embed = discord.Embed(
        title="⭕ Tic-Tac-Toe ❌",
        description=f"{interaction.user.mention} vs {opponent.mention if opponent != bot.user else 'Bot'}\n\n{' '.join(board[:3])}\n{' '.join(board[3:6])}\n{' '.join(board[6:])}\n\nUse positions 1-9 to play!",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"{interaction.user.display_name}'s turn")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="playttt", description="Make a move in Tic-Tac-Toe")
async def playttt(interaction: discord.Interaction, position: int):
    if position < 1 or position > 9:
        embed = discord.Embed(
            title="❌ Invalid Position",
            description="Choose a position between 1 and 9",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    channel_id = str(interaction.channel.id)
    games = load_games()
    game_key = f"ttt_{channel_id}"
    
    if game_key not in games:
        embed = discord.Embed(
            title="❌ No Active Game",
            description="Start a game with `/tictactoe` first!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    game = games[game_key]
    board = game['board']
    current_player = game['current']
    
    if str(interaction.user.id) != current_player and game['player2'] != 'bot':
        embed = discord.Embed(
            title="⏳ Not Your Turn",
            description="Wait for your opponent!",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    idx = position - 1
    if board[idx] != '⬜':
        embed = discord.Embed(
            title="❌ Position Taken",
            description="That spot is already occupied!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    # Determine symbol
    if current_player == game['player1']:
        symbol = game['p1_symbol']
        next_player = game['player2']
    else:
        symbol = game['p2_symbol']
        next_player = game['player1']
    
    board[idx] = symbol
    game['board'] = board
    game['current'] = next_player
    
    # Check for win
    win_conditions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
        [0, 4, 8], [2, 4, 6]  # diagonals
    ]
    
    winner = None
    for condition in win_conditions:
        if board[condition[0]] == board[condition[1]] == board[condition[2]] != '⬜':
            winner = current_player
            break
    
    if not winner and '⬜' not in board:
        winner = 'tie'
    
    if winner:
        if winner == 'tie':
            result_text = "It's a tie! 🤝"
            color = discord.Color.orange()
        else:
            winner_mention = f"<@{winner}>" if winner != 'bot' else 'Bot'
            result_text = f"{winner_mention} wins! 🎉"
            color = discord.Color.green()
        
        embed = discord.Embed(
            title="⭕ Tic-Tac-Toe - Game Over ❌",
            description=f"{' '.join(board[:3])}\n{' '.join(board[3:6])}\n{' '.join(board[6:])}\n\n{result_text}",
            color=color
        )
        del games[game_key]
        save_games(games)
    else:
        # Bot's turn if playing against bot
        if game['player2'] == 'bot' and next_player == 'bot':
            empty_positions = [i for i, spot in enumerate(board) if spot == '⬜']
            if empty_positions:
                bot_move = random.choice(empty_positions)
                board[bot_move] = game['p2_symbol']
                game['board'] = board
                game['current'] = game['player1']
                
                # Check bot win
                for condition in win_conditions:
                    if board[condition[0]] == board[condition[1]] == board[condition[2]] != '⬜':
                        winner = 'bot'
                        break
                
                if not winner and '⬜' not in board:
                    winner = 'tie'
                
                if winner:
                    if winner == 'tie':
                        result_text = "It's a tie! 🤝"
                        color = discord.Color.orange()
                    else:
                        result_text = "Bot wins! 🤖"
                        color = discord.Color.red()
                    
                    embed = discord.Embed(
                        title="⭕ Tic-Tac-Toe - Game Over ❌",
                        description=f"{' '.join(board[:3])}\n{' '.join(board[3:6])}\n{' '.join(board[6:])}\n\n{result_text}",
                        color=color
                    )
                    del games[game_key]
                    save_games(games)
                    await interaction.response.send_message(embed=embed)
                    return
        
        next_mention = f"<@{next_player}>" if next_player != 'bot' else 'Bot'
        embed = discord.Embed(
            title="⭕ Tic-Tac-Toe ❌",
            description=f"{' '.join(board[:3])}\n{' '.join(board[3:6])}\n{' '.join(board[6:])}\n\n{next_mention}'s turn",
            color=discord.Color.blue()
        )
        save_games(games)
    
    await interaction.response.send_message(embed=embed)

WORDLE_WORDS = ['apple', 'beach', 'brain', 'chair', 'dance', 'eagle', 'flame', 'grape', 'heart', 'image']

@bot.tree.command(name="wordle", description="Start a Wordle-like game")
async def wordle(interaction: discord.Interaction):
    word = random.choice(WORDLE_WORDS).upper()
    games = load_games()
    games[f"wordle_{interaction.channel.id}"] = {'word': word, 'attempts': 0, 'max': 6}
    save_games(games)
    
    embed = discord.Embed(
        title="🟩 Wordle 🟨",
        description=f"Guess the 5-letter word!\nYou have **6** attempts.\n\nType `/guessword YOURGUESS` to play!",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="guessword", description="Submit your Wordle guess")
async def guessword(interaction: discord.Interaction, guess: str):
    if len(guess) != 5:
        embed = discord.Embed(
            title="❌ Invalid Guess",
            description="Word must be exactly 5 letters!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    channel_id = str(interaction.channel.id)
    games = load_games()
    game_key = f"wordle_{channel_id}"
    
    if game_key not in games:
        embed = discord.Embed(
            title="❌ No Active Game",
            description="Start a game with `/wordle` first!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    game = games[game_key]
    target = game['word']
    guess = guess.upper()
    game['attempts'] += 1
    
    # Calculate feedback
    result = []
    target_list = list(target)
    guess_list = list(guess)
    feedback = ['⬛'] * 5
    
    # First pass: find greens (correct position)
    for i in range(5):
        if guess_list[i] == target_list[i]:
            feedback[i] = '🟩'
            target_list[i] = None
            guess_list[i] = None
    
    # Second pass: find yellows (wrong position)
    for i in range(5):
        if guess_list[i] and guess_list[i] in target_list:
            feedback[i] = '🟨'
            target_list[target_list.index(guess_list[i])] = None
    
    feedback_str = ''.join(feedback)
    
    if guess == target:
        embed = discord.Embed(
            title="🎉 Correct!",
            description=f"**{guess}**\n{feedback_str}\n\nYou won in **{game['attempts']}** attempts!",
            color=discord.Color.green()
        )
        del games[game_key]
        save_games(games)
    elif game['attempts'] >= game['max']:
        embed = discord.Embed(
            title="😔 Game Over",
            description=f"The word was **{target}**\n\nYour last guess: **{guess}**\n{feedback_str}",
            color=discord.Color.red()
        )
        del games[game_key]
        save_games(games)
    else:
        embed = discord.Embed(
            title=f"Attempt {game['attempts']}/6",
            description=f"**{guess}**\n{feedback_str}\n\n🟩 = Correct position\n🟨 = Wrong position\n⬛ = Not in word",
            color=discord.Color.blue()
        )
        save_games(games)
    
    await interaction.response.send_message(embed=embed)

HANGMAN_WORDS = ['python', 'discord', 'gaming', 'robot', 'coding', 'server', 'member', 'channel']

@bot.tree.command(name="hangman", description="Start a Hangman game")
async def hangman(interaction: discord.Interaction):
    word = random.choice(HANGMAN_WORDS).upper()
    display = '_ ' * len(word)
    games = load_games()
    games[f"hangman_{interaction.channel.id}"] = {
        'word': word,
        'guessed': [],
        'wrong': 0,
        'max_wrong': 6
    }
    save_games(games)
    
    hangman_art = [
        "```\n  +---+\n      |\n      |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n      |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n  |   |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n /|   |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n /|\\  |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n /|\\  |\n /    |\n     ===```",
        "```\n  +---+\n  O   |\n /|\\  |\n / \\  |\n     ===```"
    ]
    
    embed = discord.Embed(
        title="🪢 Hangman",
        description=f"{hangman_art[0]}\n\nWord: **{display}**\n\nWrong guesses: 0/6\n\nUse `/guessletter LETTER` to guess!",
        color=discord.Color.purple()
    )
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="guessletter", description="Guess a letter in Hangman")
async def guessletter(interaction: discord.Interaction, letter: str):
    if len(letter) != 1 or not letter.isalpha():
        embed = discord.Embed(
            title="❌ Invalid Guess",
            description="Please guess a single letter!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    channel_id = str(interaction.channel.id)
    games = load_games()
    game_key = f"hangman_{channel_id}"
    
    if game_key not in games:
        embed = discord.Embed(
            title="❌ No Active Game",
            description="Start a game with `/hangman` first!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    game = games[game_key]
    letter = letter.upper()
    
    if letter in game['guessed']:
        embed = discord.Embed(
            title="⚠️ Already Guessed",
            description=f"You already guessed **{letter}**!",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    game['guessed'].append(letter)
    
    if letter not in game['word']:
        game['wrong'] += 1
    
    # Build display
    display = ' '.join([c if c in game['guessed'] else '_' for c in game['word']])
    
    hangman_art = [
        "```\n  +---+\n      |\n      |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n      |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n  |   |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n /|   |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n /|\\  |\n      |\n     ===```",
        "```\n  +---+\n  O   |\n /|\\  |\n /    |\n     ===```",
        "```\n  +---+\n  O   |\n /|\\  |\n / \\  |\n     ===```"
    ]
    
    if '_' not in display:
        embed = discord.Embed(
            title="🎉 You Won!",
            description=f"{hangman_art[game['wrong']]}\n\nThe word was **{game['word']}**!",
            color=discord.Color.green()
        )
        del games[game_key]
        save_games(games)
    elif game['wrong'] >= game['max_wrong']:
        embed = discord.Embed(
            title="😔 Game Over",
            description=f"{hangman_art[game['wrong']]}\n\nThe word was **{game['word']}**!",
            color=discord.Color.red()
        )
        del games[game_key]
        save_games(games)
    else:
        guessed_letters = ', '.join(sorted(game['guessed']))
        embed = discord.Embed(
            title="🪢 Hangman",
            description=f"{hangman_art[game['wrong']]}\n\nWord: **{display}**\n\nGuessed: {guessed_letters}\nWrong: {game['wrong']}/{game['max_wrong']}",
            color=discord.Color.purple()
        )
        save_games(games)
    
    await interaction.response.send_message(embed=embed)

QUIZ_QUESTIONS = [
    {"q": "What does CPU stand for?", "options": ["Central Process Unit", "Central Processing Unit", "Computer Personal Unit", "Central Processor Unit"], "correct": 1},
    {"q": "Which language runs in a web browser?", "options": ["Java", "C", "Python", "JavaScript"], "correct": 3},
    {"q": "What year was Python first released?", "options": ["1989", "1991", "1995", "2000"], "correct": 1},
    {"q": "What is the largest mammal?", "options": ["Elephant", "Blue Whale", "Giraffe", "Hippopotamus"], "correct": 1},
    {"q": "How many continents are there?", "options": ["5", "6", "7", "8"], "correct": 2},
]

@bot.tree.command(name="quiz", description="Start a quick quiz")
async def quiz(interaction: discord.Interaction):
    question = random.choice(QUIZ_QUESTIONS)
    
    games = load_games()
    games[f"quiz_{interaction.channel.id}"] = {'correct': question['correct'], 'active': True}
    save_games(games)
    
    embed = discord.Embed(
        title="🧠 Quick Quiz!",
        description=f"**{question['q']}**",
        color=discord.Color.blue()
    )
    
    for i, option in enumerate(question['options']):
        emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣'][i]
        embed.add_field(name=f"{emoji}", value=option, inline=False)
    
    embed.set_footer(text="React with the number emoji to answer!")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="memory", description="Test your memory!")
async def memory(interaction: discord.Interaction):
    items = ['🍎', '🍌', '🍇', '🍊', '🍓', '🫐', '🥝', '🍒']
    sequence = random.sample(items, 4)
    
    games = load_games()
    games[f"memory_{interaction.user.id}"] = {'sequence': sequence, 'step': 0}
    save_games(games)
    
    # Show sequence
    embed = discord.Embed(
        title="🧠 Memory Game",
        description=f"Remember this sequence:\n\n**{' '.join(sequence)}**",
        color=discord.Color.purple()
    )
    embed.set_footer(text="I'll hide it in 5 seconds...")
    
    msg = await interaction.response.send_message(embed=embed)
    
    # Wait and edit
    await asyncio.sleep(5)
    
    embed2 = discord.Embed(
        title="🧠 Memory Game",
        description="What was the sequence?\n\nType the emojis in order using `/memoryguess`",
        color=discord.Color.blue()
    )
    
    try:
        original_msg = await interaction.original_response()
        await original_msg.edit(embed=embed2)
    except:
        await interaction.followup.send(embed=embed2)

@bot.tree.command(name="memoryguess", description="Submit your memory guess")
async def memoryguess(interaction: discord.Interaction, guess: str):
    user_id = str(interaction.user.id)
    games = load_games()
    
    if f"memory_{user_id}" not in games:
        embed = discord.Embed(
            title="❌ No Active Game",
            description="Start a game with `/memory` first!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return
    
    game = games[f"memory_{user_id}"]
    guess_clean = guess.replace(' ', '')
    sequence_str = ''.join(game['sequence'])
    
    if guess_clean == sequence_str:
        embed = discord.Embed(
            title="🎉 Correct!",
            description=f"The sequence was: **{' '.join(game['sequence'])}**\nGreat memory!",
            color=discord.Color.green()
        )
        del games[f"memory_{user_id}"]
        save_games(games)
    else:
        embed = discord.Embed(
            title="❌ Wrong!",
            description=f"You guessed: {guess}\nCorrect was: **{' '.join(game['sequence'])}**",
            color=discord.Color.red()
        )
        del games[f"memory_{user_id}"]
        save_games(games)
    
    await interaction.response.send_message(embed=embed)

# ============================================================================
# TRADITIONAL TEXT COMMANDS (for backward compatibility)
# ============================================================================

@bot.command(name="help")
async def traditional_help(ctx):
    embed = discord.Embed(
        title="🤖 Bot Help Menu",
        description="Use `/` commands for the best experience!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Slash Commands", value="Type `/` to see all available commands", inline=False)
    await ctx.send(embed=embed)

# ============================================================================
# RUN BOT
# ============================================================================

if __name__ == "__main__":
    # Replace with your bot token or use environment variable
    TOKEN = os.getenv("DISCORD_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    
    if TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Please set your bot token!")
        print("   Option 1: Set DISCORD_BOT_TOKEN environment variable")
        print("   Option 2: Replace YOUR_BOT_TOKEN_HERE in the code")
        print("\nGet your token from: https://discord.com/developers/applications")
    else:
        bot.run(TOKEN)
