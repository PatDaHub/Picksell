# Multi-Use Discord Bot

A feature-rich, multi-purpose Discord bot with moderation tools, level system, fun commands, and more!

## 🚀 Features

### 📋 General Commands
- `/ping` - Check bot latency
- `/userinfo` - Get detailed information about any user
- `/serverinfo` - Get comprehensive server statistics
- `/avatar` - View user avatars in full size
- `/help` - Display the help menu

### 🎮 Fun Commands
- `/roll [sides]` - Roll a dice (default 6 sides, max 1000)
- `/flip` - Flip a coin (Heads or Tails)
- `/8ball <question>` - Ask the magic 8-ball for advice
- `/say <text>` - Make the bot say something (requires Manage Messages)

### 🛡️ Moderation Commands
- `/kick <member> [reason]` - Kick a member from the server
- `/ban <member> [reason]` - Ban a member from the server
- `/warn <member> <reason>` - Issue a warning to a member
- `/warnings <member>` - View all warnings for a member
- `/clearwarnings <member>` - Clear all warnings for a member

### 📈 Level System
- Automatic XP tracking (10 XP per message)
- Level up every 100 XP
- `/level [member]` - Check your or another user's level
- `/leaderboard` - View the top 10 users by level
- Level-up announcements

### 🤖 Auto Features
- **Welcome Messages** - Automatically welcomes new members
- **Profanity Filter** - Basic auto-moderation (customizable)
- **XP Tracking** - Passive level system based on activity

## 📦 Installation

### Prerequisites
- Python 3.8+ installed
- A Discord Bot Token ([Get it here](https://discord.com/developers/applications))

### Step 1: Install Dependencies

```bash
pip install discord.py
```

### Step 2: Set Up Your Bot Token

**Option A: Environment Variable (Recommended)**
```bash
export DISCORD_BOT_TOKEN="your_bot_token_here"
```

**Option B: Edit the Code**
Replace `YOUR_BOT_TOKEN_HERE` in `discord_bot.py` with your actual token.

### Step 3: Run the Bot

```bash
python discord_bot.py
```

## 🔧 Configuration

### Required Discord Intents
Make sure these intents are enabled in your [Discord Developer Portal](https://discord.com/developers/applications):
- ✅ Message Content Intent
- ✅ Server Members Intent
- ✅ Presence Intent (optional)

### Customizing Profanity Filter
Edit the `PROFANITY_LIST` in `discord_bot.py`:
```python
PROFANITY_LIST = ['word1', 'word2', 'word3']  # Add your own list
```

### Adjusting Level System
Modify XP values in the `handle_level_system()` function:
- Current: 10 XP per message, level up every 100 XP

## 📁 File Structure

```
/workspace
├── discord_bot.py      # Main bot code
├── warnings.json       # Auto-generated: Stores user warnings
├── levels.json         # Auto-generated: Stores level data
└── README.md           # This file
```

## 🎯 Usage Examples

### Moderation
```
/kick @user Spamming
/ban @user Violation of rules
/warn @user Please be respectful
```

### Fun
```
/roll 20
/flip
/8ball Will I have a good day?
```

### Info
```
/userinfo @user
/serverinfo
/level @user
/leaderboard
```

## 🔐 Permissions Required

The bot needs these permissions to function properly:
- **Manage Messages** - For moderation and auto-mod
- **Kick Members** - For kick command
- **Ban Members** - For ban command
- **Moderate Members** - For warning system
- **Send Messages** - For all responses
- **Embed Links** - For beautiful embed messages
- **Attach Files** - For avatar display
- **Read Message History** - For context

## 🛠️ Troubleshooting

### Bot not responding to slash commands?
- Make sure you've invited the bot with the `applications.commands` scope
- Try running `/help` to register commands
- Check bot permissions in your server

### Level system not working?
- Ensure "Message Content Intent" is enabled in Discord Developer Portal
- Check that the bot can read messages in the channel

### Warnings not persisting?
- Make sure the bot has write permissions in its directory
- Check that `warnings.json` isn't corrupted

## 📝 Notes

- All data is stored locally in JSON files
- Warnings are stored per-server
- Level progress is stored per-server
- The bot supports multiple servers simultaneously

## 🚀 Future Enhancements

Potential features to add:
- Music playback
- Ticket system
- Auto-role assignment
- Custom commands
- Economy system
- Giveaway functionality
- Logging system

## 📄 License

This project is open source and available for modification.

## 💡 Support

For issues or questions:
1. Check the troubleshooting section
2. Review Discord.py documentation: https://discordpy.readthedocs.io/
3. Join the Discord.py support server

---

**Enjoy your multi-use Discord bot! 🎉**
