import discord
from discord.ext import commands, tasks
from discord import app_commands
import asyncio
import random
import datetime
import json
import os
from typing import Optional

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
