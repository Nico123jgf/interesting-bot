# -*- coding: utf-8 -*-
import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime

# Bot setup with command prefix
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent if needed
intents.members = True  # Enable member intent for welcome messages

bot = commands.Bot(command_prefix='!', intents=intents)

# Log function
async def send_log(guild, title, description, color=discord.Color.blue(), user=None, additional_fields=None):
    """Send a log message to the log channel"""
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    
    if log_channel:
        try:
            embed = discord.Embed(
                title=f"📋 {title}",
                description=description,
                color=color,
                timestamp=datetime.utcnow()
            )
            
            if user:
                embed.set_author(
                    name=f"{user.display_name} ({user.name})",
                    icon_url=user.avatar.url if user.avatar else user.default_avatar.url
                )
                embed.add_field(name="User ID", value=user.id, inline=True)
            
            if additional_fields:
                for field in additional_fields:
                    embed.add_field(
                        name=field.get("name", "Field"),
                        value=field.get("value", "No value"),
                        inline=field.get("inline", True)
                    )
            
            embed.set_footer(text=f"Server: {guild.name}")
            
            await log_channel.send(embed=embed)
        except Exception as e:
            print(f"Failed to send log: {e}")
    else:
        print(f"Log channel not found (ID: {LOG_CHANNEL_ID})")

# Configuration
WELCOME_CHANNEL_ID = 1125419386220585023  # Welcome channel
REVIEW_CHANNEL_ID = 1380480944011612170   # Review channel
LOG_CHANNEL_ID = 1252776840850964501      # Log channel
TICKET_CHANNEL_ID = 1379495376708440074   # Ticket creation channel
TICKET_CATEGORY_ID = 1383361163399528478  # Category for tickets

@bot.event
async def on_member_join(member):
    """Welcome new members with enhanced embed"""
    welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    
    if welcome_channel:
        try:
            # Create welcome embed
            embed = discord.Embed(
                title="👋 Welcome!",
                description=f"Hey {member.mention}, welcome to **{member.guild.name}**!\nWelcome to the best roblox gambling sites!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text="Enjoy your stay with us!")
            
            await welcome_channel.send(embed=embed)
            print(f"Welcomed {member.name} to the server")
            
            # Log member join
            await send_log(
                member.guild,
                "Member Joined",
                f"{member.mention} joined the server",
                color=discord.Color.green(),
                user=member,
                additional_fields=[
                    {"name": "Account Created", "value": member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), "inline": True},
                    {"name": "Member Count", "value": f"{member.guild.member_count}", "inline": True}
                ]
            )
            
        except Exception as e:
            print(f"Failed to send welcome message: {e}")
    else:
        print(f"Welcome channel not found (ID: {WELCOME_CHANNEL_ID})")

@bot.event
async def on_member_remove(member):
    """Send goodbye message when member leaves"""
    welcome_channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    
    if welcome_channel:
        try:
            # Create goodbye embed
            embed = discord.Embed(
                title="😢 Goodbye!",
                description=f"{member.name} has left the server.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
            embed.set_footer(text="Hope to see you again!")
            
            await welcome_channel.send(embed=embed)
            print(f"{member.name} left the server")
            
            # Log member leave
            await send_log(
                member.guild,
                "Member Left",
                f"{member.name} left the server",
                color=discord.Color.red(),
                user=member,
                additional_fields=[
                    {"name": "Joined Server", "value": member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC") if member.joined_at else "Unknown", "inline": True},
                    {"name": "Member Count", "value": f"{member.guild.member_count}", "inline": True}
                ]
            )
            
        except Exception as e:
            print(f"Failed to send goodbye message: {e}")
    else:
        print(f"Welcome channel not found (ID: {WELCOME_CHANNEL_ID})")

@bot.event
async def on_ready():
    """Bot startup event"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Log bot startup
    for guild in bot.guilds:
        await send_log(
            guild,
            "Bot Started",
            f"Bot {bot.user.name} has come online",
            color=discord.Color.blue(),
            additional_fields=[
                {"name": "Bot ID", "value": bot.user.id, "inline": True},
                {"name": "Guilds", "value": len(bot.guilds), "inline": True}
            ]
        )
        
        # Set up ticket panel
        await setup_ticket_panel(guild)
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

async def setup_ticket_panel(guild):
    """Set up the ticket creation panel"""
    ticket_channel = guild.get_channel(TICKET_CHANNEL_ID)
    
    if ticket_channel:
        try:
            # Check if panel already exists
            async for message in ticket_channel.history(limit=50):
                if message.author == bot.user and "🎫 Create Ticket" in message.content:
                    return  # Panel already exists
            
            # Create ticket panel embed
            embed = discord.Embed(
                title="🎫 Support Tickets",
                description="Need help? Click the button below to create a private support ticket!\n\n**What to expect:**\n• Private channel just for you\n• Staff will respond ASAP\n• Your ticket will be logged\n\n**Note:** You can only have one ticket open at a time.",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Click the button below to open a ticket")
            
            # Create view with button
            view = TicketView()
            await ticket_channel.send(embed=embed, view=view)
            
        except Exception as e:
            print(f"Failed to set up ticket panel: {e}")

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view
    
    @discord.ui.button(label='🎫 Create Ticket', style=discord.ButtonStyle.green, custom_id='create_ticket')
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_ticket_creation(interaction)

class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='🔒 Close Ticket', style=discord.ButtonStyle.red, custom_id='close_ticket')
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_ticket_close(interaction)

async def user_has_open_ticket(guild, user):
    """Check if user already has an open ticket"""
    category = guild.get_channel(TICKET_CATEGORY_ID)
    if not category:
        return False
    
    for channel in category.channels:
        if channel.topic and f"({user.id})" in channel.topic:
            return channel
    return False

async def handle_ticket_creation(interaction):
    """Handle ticket creation"""
    guild = interaction.guild
    user = interaction.user
    category = guild.get_channel(TICKET_CATEGORY_ID)
    
    if not category:
        await interaction.response.send_message("❌ Ticket category not found!", ephemeral=True)
        return
    
    # Check if user already has an open ticket
    existing_ticket = await user_has_open_ticket(guild, user)
    if existing_ticket:
        await interaction.response.send_message(f"❌ You already have an open ticket: {existing_ticket.mention}\n\nPlease close your current ticket before creating a new one.", ephemeral=True)
        return
    
    try:
        # Create private ticket channel
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }
        
        # Add permissions for roles with manage_channels permission (staff roles)
        for role in guild.roles:
            if role.permissions.manage_channels and not role.is_default():
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        
        # Create the channel
        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{user.name.lower()}-{user.discriminator}",
            category=category,
            overwrites=overwrites,
            topic=f"Ticket created by {user} ({user.id})"
        )
        
        # Create welcome embed for the ticket
        embed = discord.Embed(
            title="🎫 Support Ticket Created",
            description=f"Hello {user.mention}! Your ticket has been created.\n\nPlease describe your issue in detail and our staff will assist you shortly.",
            color=discord.Color.green()
        )
        embed.add_field(name="Ticket Creator", value=user.mention, inline=True)
        embed.add_field(name="Created", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
        embed.set_footer(text="Staff will be with you shortly!")
        
        # Send welcome message with close button
        close_view = CloseTicketView()
        await ticket_channel.send(f"{user.mention}", embed=embed, view=close_view)
        
        # Respond to interaction
        await interaction.response.send_message(f"✅ Ticket created! Please check {ticket_channel.mention}", ephemeral=True)
        
        # Log ticket creation
        await send_log(
            guild,
            "Ticket Created",
            f"New support ticket created by {user.mention}",
            color=discord.Color.green(),
            user=user,
            additional_fields=[
                {"name": "Ticket Channel", "value": ticket_channel.mention, "inline": True},
                {"name": "Category", "value": category.name, "inline": True}
            ]
        )
        
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to create ticket: {str(e)}", ephemeral=True)
        print(f"Ticket creation error: {e}")

async def handle_ticket_close(interaction):
    """Handle ticket closing"""
    if not interaction.channel.name.startswith("ticket-"):
        await interaction.response.send_message("❌ This command can only be used in ticket channels!", ephemeral=True)
        return
    
    # Extract ticket creator from channel topic or name
    ticket_creator_id = None
    if interaction.channel.topic:
        try:
            ticket_creator_id = int(interaction.channel.topic.split("(")[1].split(")")[0])
        except:
            pass
    
    ticket_creator = interaction.guild.get_member(ticket_creator_id) if ticket_creator_id else None
    
    # Check permissions (ticket creator or staff)
    has_permission = (
        interaction.user.guild_permissions.manage_channels or  # Staff
        (ticket_creator and interaction.user.id == ticket_creator.id)  # Ticket creator
    )
    
    if not has_permission:
        await interaction.response.send_message("❌ You don't have permission to close this ticket!", ephemeral=True)
        return
    
    try:
        # Create closing embed
        embed = discord.Embed(
            title="🔒 Ticket Closing",
            description="This ticket will be deleted in 10 seconds...",
            color=discord.Color.red()
        )
        embed.add_field(name="Closed by", value=interaction.user.mention, inline=True)
        embed.add_field(name="Closed at", value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>", inline=True)
        
        await interaction.response.send_message(embed=embed)
        
        # Log ticket closure
        await send_log(
            interaction.guild,
            "Ticket Closed",
            f"Support ticket closed in {interaction.channel.mention}",
            color=discord.Color.red(),
            user=interaction.user,
            additional_fields=[
                {"name": "Ticket Channel", "value": interaction.channel.name, "inline": True},
                {"name": "Original Creator", "value": ticket_creator.mention if ticket_creator else "Unknown", "inline": True}
            ]
        )
        
        # Wait 10 seconds then delete
        await asyncio.sleep(10)
        await interaction.channel.delete(reason=f"Ticket closed by {interaction.user}")
        
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to close ticket: {str(e)}", ephemeral=True)
        print(f"Ticket close error: {e}")

@bot.event
async def on_message(message):
    """Process messages and commands"""
    # Don't respond to bots
    if message.author.bot:
        return
    
    # Log messages in specific channels (optional - can be overwhelming)
    # Uncomment the lines below if you want to log all messages
    # await send_log(
    #     message.guild,
    #     "Message Sent",
    #     f"Message sent in {message.channel.mention}",
    #     color=discord.Color.light_grey(),
    #     user=message.author,
    #     additional_fields=[
    #         {"name": "Channel", "value": message.channel.mention, "inline": True},
    #         {"name": "Message Preview", "value": message.content[:100] + "..." if len(message.content) > 100 else message.content, "inline": False}
    #     ]
    # )
    
    # Process commands
    await bot.process_commands(message)

@bot.event
async def on_message_delete(message):
    """Log deleted messages"""
    if message.author.bot:
        return
        
    await send_log(
        message.guild,
        "Message Deleted",
        f"Message deleted in {message.channel.mention}",
        color=discord.Color.orange(),
        user=message.author,
        additional_fields=[
            {"name": "Channel", "value": message.channel.mention, "inline": True},
            {"name": "Deleted Content", "value": message.content[:100] + "..." if len(message.content) > 100 else message.content or "*No text content*", "inline": False}
        ]
    )

@bot.event
async def on_message_edit(before, after):
    """Log edited messages"""
    if before.author.bot or before.content == after.content:
        return
        
    await send_log(
        before.guild,
        "Message Edited",
        f"Message edited in {before.channel.mention}",
        color=discord.Color.yellow(),
        user=before.author,
        additional_fields=[
            {"name": "Channel", "value": before.channel.mention, "inline": True},
            {"name": "Before", "value": before.content[:100] + "..." if len(before.content) > 100 else before.content or "*No text content*", "inline": False},
            {"name": "After", "value": after.content[:100] + "..." if len(after.content) > 100 else after.content or "*No text content*", "inline": False}
        ]
    )

@bot.event
async def on_member_update(before, after):
    """Log member updates (nickname, roles, etc.)"""
    changes = []
    
    # Check nickname change
    if before.nick != after.nick:
        changes.append({
            "name": "Nickname Changed",
            "value": f"From: {before.nick or 'None'}\nTo: {after.nick or 'None'}",
            "inline": True
        })
    
    # Check role changes
    if before.roles != after.roles:
        added_roles = set(after.roles) - set(before.roles)
        removed_roles = set(before.roles) - set(after.roles)
        
        if added_roles:
            changes.append({
                "name": "Roles Added",
                "value": ", ".join([role.name for role in added_roles]),
                "inline": True
            })
        
        if removed_roles:
            changes.append({
                "name": "Roles Removed", 
                "value": ", ".join([role.name for role in removed_roles]),
                "inline": True
            })
    
    if changes:
        await send_log(
            after.guild,
            "Member Updated",
            f"Member {after.mention} was updated",
            color=discord.Color.purple(),
            user=after,
            additional_fields=changes
        )

@bot.event
async def on_user_update(before, after):
    """Log user updates (username, avatar, etc.)"""
    changes = []
    
    # Check username change
    if before.name != after.name:
        changes.append({
            "name": "Username Changed",
            "value": f"From: {before.name}\nTo: {after.name}",
            "inline": True
        })
    
    # Check discriminator change
    if before.discriminator != after.discriminator:
        changes.append({
            "name": "Discriminator Changed",
            "value": f"From: #{before.discriminator}\nTo: #{after.discriminator}",
            "inline": True
        })
    
    # Check avatar change
    if before.avatar != after.avatar:
        changes.append({
            "name": "Avatar Changed",
            "value": "User changed their avatar",
            "inline": True
        })
    
    if changes:
        # Log to all mutual guilds
        for guild in bot.guilds:
            if guild.get_member(after.id):
                await send_log(
                    guild,
                    "User Updated",
                    f"User {after.mention} updated their profile",
                    color=discord.Color.teal(),
                    user=after,
                    additional_fields=changes
                )

@bot.event
async def on_voice_state_update(member, before, after):
    """Log voice channel activities"""
    if before.channel != after.channel:
        if before.channel is None:
            # User joined a voice channel
            await send_log(
                member.guild,
                "Voice Channel Joined",
                f"{member.mention} joined voice channel",
                color=discord.Color.green(),
                user=member,
                additional_fields=[
                    {"name": "Channel", "value": after.channel.name, "inline": True}
                ]
            )
        elif after.channel is None:
            # User left a voice channel
            await send_log(
                member.guild,
                "Voice Channel Left",
                f"{member.mention} left voice channel",
                color=discord.Color.red(),
                user=member,
                additional_fields=[
                    {"name": "Channel", "value": before.channel.name, "inline": True}
                ]
            )
        else:
            # User moved between voice channels
            await send_log(
                member.guild,
                "Voice Channel Moved",
                f"{member.mention} moved between voice channels",
                color=discord.Color.blue(),
                user=member,
                additional_fields=[
                    {"name": "From", "value": before.channel.name, "inline": True},
                    {"name": "To", "value": after.channel.name, "inline": True}
                ]
            )

@bot.event
async def on_guild_channel_create(channel):
    """Log channel creation"""
    await send_log(
        channel.guild,
        "Channel Created",
        f"New channel created: {channel.mention}",
        color=discord.Color.green(),
        additional_fields=[
            {"name": "Channel Name", "value": channel.name, "inline": True},
            {"name": "Channel Type", "value": str(channel.type).replace('_', ' ').title(), "inline": True},
            {"name": "Category", "value": channel.category.name if channel.category else "None", "inline": True}
        ]
    )

@bot.event
async def on_guild_channel_delete(channel):
    """Log channel deletion"""
    await send_log(
        channel.guild,
        "Channel Deleted",
        f"Channel deleted: #{channel.name}",
        color=discord.Color.red(),
        additional_fields=[
            {"name": "Channel Name", "value": channel.name, "inline": True},
            {"name": "Channel Type", "value": str(channel.type).replace('_', ' ').title(), "inline": True},
            {"name": "Category", "value": channel.category.name if channel.category else "None", "inline": True}
        ]
    )

@bot.event
async def on_guild_role_create(role):
    """Log role creation"""
    await send_log(
        role.guild,
        "Role Created",
        f"New role created: @{role.name}",
        color=discord.Color.green(),
        additional_fields=[
            {"name": "Role Name", "value": role.name, "inline": True},
            {"name": "Color", "value": str(role.color), "inline": True},
            {"name": "Mentionable", "value": "Yes" if role.mentionable else "No", "inline": True}
        ]
    )

@bot.event
async def on_guild_role_delete(role):
    """Log role deletion"""
    await send_log(
        role.guild,
        "Role Deleted",
        f"Role deleted: @{role.name}",
        color=discord.Color.red(),
        additional_fields=[
            {"name": "Role Name", "value": role.name, "inline": True},
            {"name": "Color", "value": str(role.color), "inline": True},
            {"name": "Members Had Role", "value": str(len(role.members)), "inline": True}
        ]
    )

# Slash command: Review with site selection
@bot.tree.command(name='review', description='Submit a review for Luckshot.live or Coinclash.live (1-5 stars)')
async def review_slash(interaction: discord.Interaction, site: str, rating: int, feedback: str):
    """Submit a review with site selection, rating and feedback"""
    
    # Validate site selection
    valid_sites = ["luckshot.live", "coinclash.live"]
    site_lower = site.lower()
    
    if site_lower not in valid_sites:
        await interaction.response.send_message(
            f"❌ Invalid site! Please choose from: **{', '.join(valid_sites)}**", 
            ephemeral=True
        )
        return
    
    # Validate rating
    if not 1 <= rating <= 5:
        await interaction.response.send_message(
            "❌ Rating must be between 1 and 5 stars!", 
            ephemeral=True
        )
        return
    
    # Validate feedback length
    if len(feedback) > 1000:
        await interaction.response.send_message(
            "❌ Feedback must be 1000 characters or less!", 
            ephemeral=True
        )
        return
    
    if len(feedback.strip()) < 5:
        await interaction.response.send_message(
            "❌ Please provide more detailed feedback (at least 5 characters)!", 
            ephemeral=True
        )
        return
    
    # Site-specific colors and emojis
    site_config = {
        "luckshot.live": {"color": 0x00ff41, "emoji": "🍀"},
        "coinclash.live": {"color": 0xffd700, "emoji": "💰"}
    }
    
    config = site_config.get(site_lower, {"color": 0x00ff00, "emoji": "⭐"})
    
    # Create review embed
    embed = discord.Embed(
        title=f"{config['emoji']} New Review - {site_lower.title()}",
        color=config["color"] if rating >= 4 else 0xffff00 if rating >= 3 else 0xff0000,
        timestamp=datetime.utcnow()
    )
    
    # Star rating display
    stars = "⭐" * rating + "☆" * (5 - rating)
    embed.add_field(name="Rating", value=f"{stars} ({rating}/5)", inline=True)
    embed.add_field(name="Site", value=f"**{site_lower.title()}**", inline=True)
    embed.add_field(name="Reviewer", value=interaction.user.mention, inline=True)
    embed.add_field(name="Feedback", value=feedback, inline=False)
    
    embed.set_footer(
        text=f"Review for {site_lower.title()} by {interaction.user.display_name}", 
        icon_url=interaction.user.avatar.url if interaction.user.avatar else None
    )
    
    # Send confirmation to user
    await interaction.response.send_message(
        f"✅ Review submitted successfully for **{site_lower.title()}**! Thank you for your feedback.", 
        ephemeral=True
    )
    
    # Log review submission
    await send_log(
        interaction.guild,
        "Review Submitted",
        f"New review submitted by {interaction.user.mention} for {site_lower.title()}",
        color=discord.Color.gold(),
        user=interaction.user,
        additional_fields=[
            {"name": "Site", "value": site_lower.title(), "inline": True},
            {"name": "Rating", "value": f"{stars} ({rating}/5)", "inline": True},
            {"name": "Channel", "value": interaction.channel.mention, "inline": True},
            {"name": "Feedback Preview", "value": feedback[:100] + "..." if len(feedback) > 100 else feedback, "inline": False}
        ]
    )
    
    # Post review to dedicated review channel
    review_channel = interaction.guild.get_channel(REVIEW_CHANNEL_ID)
    if review_channel:
        await review_channel.send(embed=embed)
    else:
        # Fallback to current channel if review channel not found
        await interaction.followup.send(embed=embed)

# Autocomplete for site parameter
@review_slash.autocomplete('site')
async def site_autocomplete(interaction: discord.Interaction, current: str):
    sites = ["Luckshot.live", "Coinclash.live"]
    return [
        discord.app_commands.Choice(name=site, value=site.lower())
        for site in sites if current.lower() in site.lower()
    ]

# Error handling for slash commands
@bot.event
async def on_app_command_error(interaction: discord.Interaction, error):
    """Handle slash command errors"""
    if interaction.response.is_done():
        send_method = interaction.followup.send
    else:
        send_method = interaction.response.send_message
    
    embed = discord.Embed(
        title="❌ Command Error",
        description="An error occurred while processing your command.",
        color=0xff0000
    )
    
    try:
        await send_method(embed=embed, ephemeral=True)
    except:
        pass
    
    print(f'Slash command error: {error}')

# Required imports
import discord
from discord.ext import commands
import random
import asyncio
import re
from datetime import datetime, timedelta

# Giveaway storage (in-memory)
active_giveaways = {}
# Store completed giveaways for reroll functionality
completed_giveaways = {}

def parse_duration(duration_str):
    """Parse duration string like '1m', '5m', '1h', '30s' into seconds"""
    duration_str = duration_str.lower().strip()
    
    # Match patterns like: 30s, 5m, 1h, 2d
    match = re.match(r'^(\d+)([smhd])$', duration_str)
    if not match:
        return None
    
    value, unit = match.groups()
    value = int(value)
    
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    elif unit == 'd':
        return value * 86400
    
    return None

async def auto_end_giveaway(giveaway_id, duration_seconds):
    """Automatically end giveaway after specified duration"""
    await asyncio.sleep(duration_seconds)
    
    giveaway = active_giveaways.get(giveaway_id)
    if not giveaway:
        return  # Giveaway was already ended manually
    
    # Get the channel and create a mock interaction for ending
    try:
        channel = bot.get_channel(giveaway['channel_id'])
        if not channel:
            return
        
        # End the giveaway
        participants = giveaway['participants']
        winners_count = giveaway['winners']
        
        if not participants:
            embed = discord.Embed(
                title=" Giveaway Ended (Auto)",
                description=f"**Prize:** {giveaway['prize']}\n\n No one entered the giveaway!",
                color=0xff0000
            )
            await channel.send(embed=embed)
            del active_giveaways[giveaway_id]
            return
        
        # Pick winners
        winners = random.sample(participants, min(winners_count, len(participants)))
        
        # Create winners list
        winner_mentions = []
        for winner_id in winners:
            user = channel.guild.get_member(winner_id)
            if user:
                winner_mentions.append(user.mention)
        
        # Create result embed
        embed = discord.Embed(
            title=" Giveaway Ended! (Auto)",
            description=f"**Prize:** {giveaway['prize']}\n**Host:** {giveaway['host']}",
            color=0x00ff00
        )
        
        if winner_mentions:
            embed.add_field(
                name=" Winners",
                value="\n".join(winner_mentions),
                inline=False
            )
        
        embed.add_field(name="Total Participants", value=str(len(participants)), inline=True)
        embed.add_field(name="Giveaway ID", value=f"`{giveaway_id}`", inline=True)
        embed.set_footer(text="Congratulations to the winners! - Use /greroll with the Giveaway ID to reroll")
        
        await channel.send(embed=embed)
        
        # Send congratulations message
        if winner_mentions:
            congrats_msg = f" Congratulations {', '.join(winner_mentions)}! You won **{giveaway['prize']}**!"
            await channel.send(congrats_msg)
        
        # Update original giveaway message to show it ended
        try:
            if giveaway['message_id']:
                message = await channel.fetch_message(giveaway['message_id'])
                ended_embed = discord.Embed(
                    title=" GIVEAWAY ENDED ",
                    description=f"**Prize:** {giveaway['prize']}\n**Duration:** {giveaway['duration']}\n**Host:** {giveaway['host']}\n**Winners:** {giveaway['winners']}",
                    color=0xff0000
                )
                ended_embed.add_field(name="Status", value=" Ended", inline=True)
                ended_embed.add_field(name="Final Participants", value=f"{len(giveaway['participants'])} entered", inline=True)
                ended_embed.set_footer(text="This giveaway has ended!")
                await message.edit(embed=ended_embed, view=None)
        except:
            pass
        
        # Store completed giveaway for reroll functionality
        completed_giveaways[giveaway_id] = {
            'prize': giveaway['prize'],
            'host': giveaway['host'],
            'participants': giveaway['participants'].copy(),
            'winners_count': giveaway['winners'],
            'channel_id': giveaway['channel_id'],
            'completed_at': datetime.utcnow(),
            'last_winners': winners
        }
        
        # Log giveaway end
        try:
            await send_log(
                channel.guild,
                "Giveaway Auto-Ended",
                f"Giveaway automatically ended after {giveaway['duration']}",
                color=discord.Color.gold(),
                additional_fields=[
                    {"name": "Prize", "value": giveaway['prize'], "inline": True},
                    {"name": "Participants", "value": str(len(participants)), "inline": True},
                    {"name": "Winners", "value": "\n".join(winner_mentions) if winner_mentions else "None", "inline": False},
                    {"name": "Giveaway ID", "value": f"`{giveaway_id}`", "inline": True}
                ]
            )
        except Exception as e:
            print(f"Error sending log: {e}")
        
        # Remove from active giveaways
        del active_giveaways[giveaway_id]
        
    except Exception as e:
        print(f"Error auto-ending giveaway {giveaway_id}: {e}")

# Giveaway View with Enter Button
class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
    
    @discord.ui.button(label=' Enter Giveaway', style=discord.ButtonStyle.green, custom_id='enter_giveaway')
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Defer the response first to avoid timeout
        await interaction.response.defer(ephemeral=True)
        
        giveaway = active_giveaways.get(self.giveaway_id)
        if not giveaway:
            await interaction.followup.send(" This giveaway is no longer active!", ephemeral=True)
            return
        
        user_id = interaction.user.id
        if user_id in giveaway['participants']:
            await interaction.followup.send(" You're already entered in this giveaway!", ephemeral=True)
            return
        
        giveaway['participants'].append(user_id)
        await interaction.followup.send(" You've entered the giveaway! Good luck!", ephemeral=True)
        
        # Update embed with new participant count
        embed = discord.Embed(
            title=" GIVEAWAY ",
            description=f"**Prize:** {giveaway['prize']}\n**Duration:** {giveaway['duration']}\n**Host:** {giveaway['host']}\n**Winners:** {giveaway['winners']}",
            color=0x00ff00
        )
        embed.add_field(name="Participants", value=f"{len(giveaway['participants'])} entered", inline=True)
        embed.set_footer(text="Click the button below to enter!")
        
        # Get the original message and edit it
        try:
            channel = interaction.guild.get_channel(giveaway['channel_id'])
            if channel and giveaway['message_id']:
                message = await channel.fetch_message(giveaway['message_id'])
                await message.edit(embed=embed, view=self)
        except discord.NotFound:
            print(f"Could not find message {giveaway['message_id']} in channel {giveaway['channel_id']}")
        except discord.Forbidden:
            print("Bot doesn't have permission to edit the message")
        except Exception as e:
            print(f"Error updating giveaway message: {e}")

# Slash command: Start Giveaway
@bot.tree.command(name='giveaway', description='Start a giveaway')
async def giveaway_slash(interaction: discord.Interaction, prize: str, duration: str, winners: int = 1):
    """Start a new giveaway"""
    
    if winners < 1 or winners > 20:
        await interaction.response.send_message(" Number of winners must be between 1 and 20!", ephemeral=True)
        return
    
    if len(prize) > 100:
        await interaction.response.send_message(" Prize description must be 100 characters or less!", ephemeral=True)
        return
    
    # Parse duration
    duration_seconds = parse_duration(duration)
    if duration_seconds is None:
        await interaction.response.send_message(" Invalid duration format! Use format like: 30s, 5m, 1h, 2d", ephemeral=True)
        return
    
    if duration_seconds < 10:  # Minimum 10 seconds
        await interaction.response.send_message(" Duration must be at least 10 seconds!", ephemeral=True)
        return
    
    if duration_seconds > 86400 * 7:  # Maximum 7 days
        await interaction.response.send_message(" Duration cannot exceed 7 days!", ephemeral=True)
        return
    
    # Create giveaway ID
    giveaway_id = f"{interaction.guild.id}_{interaction.user.id}_{int(discord.utils.utcnow().timestamp())}"
    
    # Calculate end time
    end_time = datetime.utcnow() + timedelta(seconds=duration_seconds)
    
    # Store giveaway data
    active_giveaways[giveaway_id] = {
        'prize': prize,
        'duration': duration,
        'duration_seconds': duration_seconds,
        'end_time': end_time,
        'winners': winners,
        'host': interaction.user.mention,
        'participants': [],
        'channel_id': interaction.channel.id,
        'message_id': None
    }
    
    # Create giveaway embed
    embed = discord.Embed(
        title=" GIVEAWAY ",
        description=f"**Prize:** {prize}\n**Duration:** {duration}\n**Host:** {interaction.user.mention}\n**Winners:** {winners}",
        color=0x00ff00
    )
    embed.add_field(name="Participants", value="0 entered", inline=True)
    embed.add_field(name="Ends", value=f"<t:{int(end_time.timestamp())}:R>", inline=True)
    embed.set_footer(text="Click the button below to enter!")
    
    # Create view with the giveaway ID
    view = GiveawayView(giveaway_id)
    
    # Send the message
    await interaction.response.send_message(embed=embed, view=view)
    
    # Store message ID for later reference
    try:
        message = await interaction.original_response()
        active_giveaways[giveaway_id]['message_id'] = message.id
    except Exception as e:
        print(f"Error getting original response: {e}")
    
    # Start auto-end task
    asyncio.create_task(auto_end_giveaway(giveaway_id, duration_seconds))
    
    # Log giveaway creation (make sure send_log function exists)
    try:
        await send_log(
            interaction.guild,
            "Giveaway Started",
            f"New giveaway started by {interaction.user.mention}",
            color=discord.Color.gold(),
            user=interaction.user,
            additional_fields=[
                {"name": "Prize", "value": prize, "inline": True},
                {"name": "Duration", "value": duration, "inline": True},
                {"name": "Winners", "value": str(winners), "inline": True},
                {"name": "Channel", "value": interaction.channel.mention, "inline": True},
                {"name": "Giveaway ID", "value": f"`{giveaway_id}`", "inline": True}
            ]
        )
    except Exception as e:
        print(f"Error sending log: {e}")

# Slash command: End Giveaway
@bot.tree.command(name='gend', description='End a giveaway and pick winners')
async def end_giveaway_slash(interaction: discord.Interaction):
    """End the most recent giveaway in this channel"""
    
    # Find giveaway in this channel
    giveaway_id = None
    giveaway_data = None
    
    for gid, gdata in active_giveaways.items():
        if gdata['channel_id'] == interaction.channel.id:
            giveaway_id = gid
            giveaway_data = gdata
            break
    
    if not giveaway_data:
        await interaction.response.send_message(" No active giveaway found in this channel!", ephemeral=True)
        return
    
    # Check if user is host or has manage messages permission
    is_host = interaction.user.mention == giveaway_data['host']
    has_permission = interaction.user.guild_permissions.manage_messages
    
    if not (is_host or has_permission):
        await interaction.response.send_message(" Only the giveaway host or staff can end this giveaway!", ephemeral=True)
        return
    
    await end_giveaway(interaction, giveaway_id, giveaway_data)

async def end_giveaway(interaction, giveaway_id, giveaway_data):
    """End a giveaway and pick winners"""
    
    participants = giveaway_data['participants']
    winners_count = giveaway_data['winners']
    
    if not participants:
        embed = discord.Embed(
            title=" Giveaway Ended",
            description=f"**Prize:** {giveaway_data['prize']}\n\n No one entered the giveaway!",
            color=0xff0000
        )
        await interaction.response.send_message(embed=embed)
        del active_giveaways[giveaway_id]
        return
    
    # Pick winners
    import random
    winners = random.sample(participants, min(winners_count, len(participants)))
    
    # Create winners list
    winner_mentions = []
    for winner_id in winners:
        user = interaction.guild.get_member(winner_id)
        if user:
            winner_mentions.append(user.mention)
    
    # Create result embed
    embed = discord.Embed(
        title=" Giveaway Ended!",
        description=f"**Prize:** {giveaway_data['prize']}\n**Host:** {giveaway_data['host']}",
        color=0x00ff00
    )
    
    if winner_mentions:
        embed.add_field(
            name=" Winners",
            value="\n".join(winner_mentions),
            inline=False
        )
    
    embed.add_field(name="Total Participants", value=str(len(participants)), inline=True)
    embed.add_field(name="Giveaway ID", value=f"`{giveaway_id}`", inline=True)
    embed.set_footer(text="Congratulations to the winners! - Use /greroll with the Giveaway ID to reroll")
    
    await interaction.response.send_message(embed=embed)
    
    # Send congratulations message
    if winner_mentions:
        congrats_msg = f" Congratulations {', '.join(winner_mentions)}! You won **{giveaway_data['prize']}**!"
        await interaction.followup.send(congrats_msg)
    
    # Store completed giveaway for reroll functionality
    completed_giveaways[giveaway_id] = {
        'prize': giveaway_data['prize'],
        'host': giveaway_data['host'],
        'participants': giveaway_data['participants'].copy(),
        'winners_count': giveaway_data['winners'],
        'channel_id': giveaway_data['channel_id'],
        'completed_at': datetime.utcnow(),
        'last_winners': winners
    }
    
    # Log giveaway end
    try:
        await send_log(
            interaction.guild,
            "Giveaway Ended",
            f"Giveaway ended by {interaction.user.mention}",
            color=discord.Color.gold(),
            user=interaction.user,
            additional_fields=[
                {"name": "Prize", "value": giveaway_data['prize'], "inline": True},
                {"name": "Participants", "value": str(len(participants)), "inline": True},
                {"name": "Winners", "value": "\n".join(winner_mentions) if winner_mentions else "None", "inline": False},
                {"name": "Giveaway ID", "value": f"`{giveaway_id}`", "inline": True}
            ]
        )
    except Exception as e:
        print(f"Error sending log: {e}")
    
    # Remove from active giveaways
    del active_giveaways[giveaway_id]

# Slash command: Reroll Giveaway Winners
@bot.tree.command(name='greroll', description='Reroll winners for a completed giveaway')
async def reroll_giveaway_slash(interaction: discord.Interaction, giveaway_id: str):
    """Reroll winners for a completed giveaway using the giveaway ID"""
    
    # Clean the giveaway ID (remove backticks if present)
    giveaway_id = giveaway_id.strip('`')
    
    # Check if giveaway exists in completed giveaways
    if giveaway_id not in completed_giveaways:
        await interaction.response.send_message(" Invalid giveaway ID or giveaway not found! Make sure you're using the correct Giveaway ID from a completed giveaway.", ephemeral=True)
        return
    
    giveaway_data = completed_giveaways[giveaway_id]
    
    # Check if user has permission to reroll (host or manage messages)
    is_host = interaction.user.mention == giveaway_data['host']
    has_permission = interaction.user.guild_permissions.manage_messages
    
    if not (is_host or has_permission):
        await interaction.response.send_message(" Only the giveaway host or staff can reroll this giveaway!", ephemeral=True)
        return
    
    # Check if giveaway is in the same channel (optional security check)
    if giveaway_data['channel_id'] != interaction.channel.id:
        await interaction.response.send_message(" You can only reroll giveaways in the channel where they were originally held!", ephemeral=True)
        return
    
    participants = giveaway_data['participants']
    winners_count = giveaway_data['winners_count']
    
    if not participants:
        await interaction.response.send_message(" Cannot reroll - no participants were in this giveaway!", ephemeral=True)
        return
    
    # Pick new winners (exclude previous winners to avoid duplicates if possible)
    available_participants = participants.copy()
    
    # Try to exclude previous winners if there are enough participants
    if len(participants) > winners_count and 'last_winners' in giveaway_data:
        available_participants = [p for p in participants if p not in giveaway_data['last_winners']]
        if len(available_participants) < winners_count:
            # If not enough new participants, use all participants
            available_participants = participants.copy()
    
    # Pick new winners
    new_winners = random.sample(available_participants, min(winners_count, len(available_participants)))
    
    # Create winners list
    winner_mentions = []
    for winner_id in new_winners:
        user = interaction.guild.get_member(winner_id)
        if user:
            winner_mentions.append(user.mention)
    
    # Create reroll result embed
    embed = discord.Embed(
        title=" Giveaway Rerolled!",
        description=f"**Prize:** {giveaway_data['prize']}\n**Original Host:** {giveaway_data['host']}\n**Rerolled by:** {interaction.user.mention}",
        color=0x9932cc
    )
    
    if winner_mentions:
        embed.add_field(
            name=" New Winners",
            value="\n".join(winner_mentions),
            inline=False
        )
    
    embed.add_field(name="Total Participants", value=str(len(participants)), inline=True)
    embed.add_field(name="Giveaway ID", value=f"`{giveaway_id}`", inline=True)
    embed.set_footer(text="New winners have been selected!")
    
    await interaction.response.send_message(embed=embed)
    
    # Send congratulations message to new winners
    if winner_mentions:
        congrats_msg = f" Congratulations {', '.join(winner_mentions)}! You won **{giveaway_data['prize']}** (Reroll)!"
        await interaction.followup.send(congrats_msg)
    
    # Update the stored data with new winners
    completed_giveaways[giveaway_id]['last_winners'] = new_winners
    completed_giveaways[giveaway_id]['last_reroll'] = datetime.utcnow()
    completed_giveaways[giveaway_id]['rerolled_by'] = interaction.user.mention
    
    # Log giveaway reroll
    try:
        await send_log(
            interaction.guild,
            "Giveaway Rerolled",
            f"Giveaway winners rerolled by {interaction.user.mention}",
            color=discord.Color.purple(),
            user=interaction.user,
            additional_fields=[
                {"name": "Prize", "value": giveaway_data['prize'], "inline": True},
                {"name": "Original Host", "value": giveaway_data['host'], "inline": True},
                {"name": "New Winners", "value": "\n".join(winner_mentions) if winner_mentions else "None", "inline": False},
                {"name": "Giveaway ID", "value": f"`{giveaway_id}`", "inline": True}
            ]
        )
    except Exception as e:
        print(f"Error sending reroll log: {e}")

# Slash command: List Recent Giveaways (for finding IDs)
@bot.tree.command(name='glist', description='List recent completed giveaways in this channel')
async def list_giveaways_slash(interaction: discord.Interaction):
    """List recent completed giveaways in this channel with their IDs"""
    
    # Filter giveaways for this channel
    channel_giveaways = {
        gid: gdata for gid, gdata in completed_giveaways.items() 
        if gdata['channel_id'] == interaction.channel.id
    }
    
    if not channel_giveaways:
        await interaction.response.send_message(" No completed giveaways found in this channel!", ephemeral=True)
        return
    
    # Sort by completion date (most recent first)
    sorted_giveaways = sorted(
        channel_giveaways.items(), 
        key=lambda x: x[1]['completed_at'], 
        reverse=True
    )
    
    # Take only the most recent 10
    recent_giveaways = sorted_giveaways[:10]
    
    embed = discord.Embed(
        title=" Recent Completed Giveaways",
        description="Here are the most recent completed giveaways in this channel:",
        color=0x3498db
    )
    
    for i, (gid, gdata) in enumerate(recent_giveaways, 1):
        completed_time = gdata['completed_at']
        time_ago = f"<t:{int(completed_time.timestamp())}:R>"
        
        reroll_info = ""
        if 'last_reroll' in gdata:
            reroll_info = f" (Last rerolled <t:{int(gdata['last_reroll'].timestamp())}:R>)"
        
        embed.add_field(
            name=f"{i}. {gdata['prize'][:50]}{'...' if len(gdata['prize']) > 50 else ''}",
            value=f"**ID:** `{gid}`\n**Host:** {gdata['host']}\n**Completed:** {time_ago}{reroll_info}",
            inline=False
        )
    
    embed.set_footer(text="Use /greroll <giveaway_id> to reroll winners - IDs are case-sensitive")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Make sure to add this to your bot's setup if using persistent views
async def setup_persistent_views(bot):
    """Setup persistent views when bot starts"""
    for giveaway_id in active_giveaways:
        bot.add_view(GiveawayView(giveaway_id))

# Guess the Number Game functionality
# Add this to your existing bot.py file

import random

# Game storage
active_number_game = None
GUESS_CHANNEL_ID = 1380764518803570768  # Channel for guessing

class NumberGame:
    def __init__(self, max_number, custom_number=None, host=None):
        self.max_number = max_number
        self.target_number = custom_number if custom_number else random.randint(1, max_number)
        self.host = host
        self.guesses = []
        self.all_guesses_count = 0  # Track total guesses made
        self.is_active = True
    
    def make_guess(self, user, guess):
        """Process a guess and return result"""
        self.guesses.append({'user': user, 'guess': guess, 'timestamp': discord.utils.utcnow()})
        self.all_guesses_count += 1  # Increment total guess counter
        
        if guess == self.target_number:
            return "correct"
        else:
            return "incorrect"

# Slash command: Start Guess the Number Game
@bot.tree.command(name='gnstart', description='Start a guess the number game (Admin only)')
async def start_number_game(interaction: discord.Interaction, max_number: int, custom_number: int = None):
    """Start a new guess the number game"""
    
    # Check if user has administrator permission
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(" You need administrator permissions to use this command!", ephemeral=True)
        return
    
    global active_number_game
    
    if active_number_game and active_number_game.is_active:
        await interaction.response.send_message(" A number guessing game is already active! Use `/gnstop` to end it first.", ephemeral=True)
        return
    
    # Validate max_number
    if max_number < 2 or max_number > 10000:
        await interaction.response.send_message(" Max number must be between 2 and 10,000!", ephemeral=True)
        return
    
    # Validate custom_number if provided
    if custom_number is not None:
        if custom_number < 1 or custom_number > max_number:
            await interaction.response.send_message(f" Custom number must be between 1 and {max_number}!", ephemeral=True)
            return
    
    # Create new game
    active_number_game = NumberGame(max_number, custom_number, interaction.user)
    
    # Create game start embed
    embed = discord.Embed(
        title=" Guess the Number Game Started!",
        description=f"I'm thinking of a number between **1** and **{max_number}**!\n\nHead over to <#{GUESS_CHANNEL_ID}> and start guessing!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Range", value=f"1 - {max_number}", inline=True)
    embed.add_field(name="Host", value=interaction.user.mention, inline=True)
    embed.add_field(name="Status", value=" Active", inline=True)
    embed.set_footer(text="Type your guess as a number in the guessing channel!")
    
    await interaction.response.send_message(embed=embed)
    
    # Send notification to guess channel
    guess_channel = interaction.guild.get_channel(GUESS_CHANNEL_ID)
    if guess_channel:
        game_embed = discord.Embed(
            title=" New Number Guessing Game!",
            description=f"Guess the number between **1** and **{max_number}**!\n\nJust type your guess as a number in this channel!",
            color=discord.Color.green()
        )
        game_embed.add_field(name="Range", value=f"1 - {max_number}", inline=True)
        game_embed.add_field(name="Host", value=interaction.user.mention, inline=True)
        game_embed.set_footer(text="Good luck everyone! ")
        
        await guess_channel.send(embed=game_embed)
    
    # Log game start
    await send_log(
        interaction.guild,
        "Number Game Started",
        f"Guess the number game started by {interaction.user.mention}",
        color=discord.Color.blue(),
        user=interaction.user,
        additional_fields=[
            {"name": "Range", "value": f"1 - {max_number}", "inline": True},
            {"name": "Custom Number", "value": "Yes" if custom_number else "No", "inline": True},
            {"name": "Channel", "value": f"<#{GUESS_CHANNEL_ID}>", "inline": True}
        ]
    )

# Slash command: Stop Guess the Number Game
@bot.tree.command(name='gnstop', description='Stop the active number guessing game (Admin only)')
async def stop_number_game(interaction: discord.Interaction):
    """Stop the active number guessing game"""
    
    # Check if user has administrator permission
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message(" You need administrator permissions to use this command!", ephemeral=True)
        return
    
    global active_number_game
    
    if not active_number_game or not active_number_game.is_active:
        await interaction.response.send_message(" No active number guessing game found!", ephemeral=True)
        return
    
    # End the game
    active_number_game.is_active = False
    target_number = active_number_game.target_number
    total_guesses = active_number_game.all_guesses_count
    
    # Create game end embed
    embed = discord.Embed(
        title=" Number Guessing Game Stopped!",
        description=f"The game has been ended by {interaction.user.mention}",
        color=discord.Color.red()
    )
    embed.add_field(name="The Number Was", value=f"**{target_number}**", inline=True)
    embed.add_field(name="Total Guesses", value=str(total_guesses), inline=True)
    embed.add_field(name="Host", value=active_number_game.host.mention, inline=True)
    embed.set_footer(text="Game ended by administrator")
    
    await interaction.response.send_message(embed=embed)
    
    # Send notification to guess channel
    guess_channel = interaction.guild.get_channel(GUESS_CHANNEL_ID)
    if guess_channel:
        end_embed = discord.Embed(
            title=" Game Ended!",
            description=f"The number guessing game has been stopped by an administrator.\n\n**The number was: {target_number}**",
            color=discord.Color.red()
        )
        end_embed.add_field(name="Total Guesses Made", value=str(total_guesses), inline=True)
        end_embed.set_footer(text="Better luck next time!")
        
        await guess_channel.send(embed=end_embed)
    
    # Log game stop
    await send_log(
        interaction.guild,
        "Number Game Stopped",
        f"Number guessing game stopped by {interaction.user.mention}",
        color=discord.Color.red(),
        user=interaction.user,
        additional_fields=[
            {"name": "The Number", "value": str(target_number), "inline": True},
            {"name": "Total Guesses", "value": str(total_guesses), "inline": True},
            {"name": "Game Host", "value": active_number_game.host.mention, "inline": True}
        ]
    )
    
    # Clear the game
    active_number_game = None

# Add this to your existing on_message event handler
# Modify your existing on_message function to include this logic:

# IMPORTANT: Add this code to your EXISTING on_message function, don't replace it!
# Add this section at the beginning of your existing on_message function:

async def handle_number_guess(message):
    """Handle number guessing logic"""
    global active_number_game
    
    # Check for number guessing in the specific channel
    if message.channel.id == GUESS_CHANNEL_ID and active_number_game and active_number_game.is_active:
        # Check if message is a number
        try:
            guess = int(message.content.strip())
            print(f"DEBUG: User {message.author} guessed {guess}, target is {active_number_game.target_number}")
            
            # Validate guess range
            if guess < 1 or guess > active_number_game.max_number:
                embed = discord.Embed(
                    title=" Invalid Guess",
                    description=f"Please guess a number between **1** and **{active_number_game.max_number}**!",
                    color=discord.Color.red()
                )
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                await message.reply(embed=embed, mention_author=False)
                return True  # Return True to indicate we handled this message
            
            # Process the guess - FIXED: This actually increments the counter
            active_number_game.guesses.append({
                'user': message.author, 
                'guess': guess, 
                'timestamp': discord.utils.utcnow()
            })
            active_number_game.all_guesses_count += 1
            
            print(f"DEBUG: Total guesses now: {active_number_game.all_guesses_count}")
            
            # Check if correct
            if guess == active_number_game.target_number:
                print("DEBUG: CORRECT GUESS!")
                # Winner!
                active_number_game.is_active = False
                
                embed = discord.Embed(
                    title=" WINNER!",
                    description=f"Congratulations {message.author.mention}!\n\nYou guessed the correct number: **{guess}**!",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Your Guess", value=str(guess), inline=True)
                embed.add_field(name="Total Guesses Made", value=str(active_number_game.all_guesses_count), inline=True)
                embed.add_field(name="Game Host", value=active_number_game.host.mention, inline=True)
                embed.set_author(name=f" {message.author.display_name}", icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
                embed.set_footer(text="Excellent guessing! ")
                
                await message.reply(embed=embed, mention_author=True)
                
                # Log the win
                try:
                    await send_log(
                        message.guild,
                        "Number Game Won",
                        f"{message.author.mention} won the number guessing game!",
                        color=discord.Color.gold(),
                        user=message.author,
                        additional_fields=[
                            {"name": "Winning Number", "value": str(guess), "inline": True},
                            {"name": "Total Guesses", "value": str(active_number_game.all_guesses_count), "inline": True},
                            {"name": "Game Host", "value": active_number_game.host.mention, "inline": True}
                        ]
                    )
                except Exception as e:
                    print(f"DEBUG: Error logging win: {e}")
                
                # Clear the game
                active_number_game = None
                
            # If incorrect, do nothing - stay silent
            return True  # Return True to indicate we handled this message
                
        except ValueError:
            # Not a number, ignore
            pass
    
    return False  # Return False if we didn't handle the message

# MODIFY YOUR EXISTING on_message FUNCTION LIKE THIS:
@bot.event
async def on_message(message):
    """Process messages and commands"""
    # Don't respond to bots
    if message.author.bot:
        return
    
    # Handle number guessing first
    if await handle_number_guess(message):
        return  # If we handled a guess, don't process other commands
    
    # Your existing message processing code here...
    # Process commands
    await bot.process_commands(message)

@bot.event
async def on_member_ban(guild, user):
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return
    
    # Get audit log to find who made the ban
    async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
        if entry.target.id == user.id:
            embed = discord.Embed(
                title="Member Banned",
                color=discord.Color.red(),
                timestamp=entry.created_at
            )
            embed.add_field(name="Banned User", value=f"{user} ({user.id})", inline=False)
            embed.add_field(name="Banned By", value=f"{entry.user} ({entry.user.id})", inline=False)
            if entry.reason:
                embed.add_field(name="Reason", value=entry.reason, inline=False)
            
            await log_channel.send(embed=embed)
            break            

import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Application system configuration
APPLY_CHANNEL_ID = 1379879557984944270
STAFF_CHANNEL_ID = 1380229490617352391
STAFF_ROLE_ID = 1380228782606127265

# Store active applications
active_applications = {}

# Application questions
QUESTIONS = [
    "What's your age and timezone?",
    "How active are you on Discord daily? (hours per day)",
    "Do you have any previous moderation experience? If yes, please describe.",
    "Why do you want to join our staff team?",
    "How would you handle a conflict between two members?",
    "What would you do if you're unsure about a moderation decision?",
    "Are you available for staff meetings and events?",
    "What additional skills would you bring to the team?",
    "If you were a Discord bot, what would your most useless command be?",
    "You're trapped in a Discord server forever - which emoji would you choose as your companion and why?"
]

class ApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Apply Now', style=discord.ButtonStyle.primary, emoji='📋', custom_id='start_application')
    async def apply_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if user_id in active_applications:
            await interaction.response.send_message('❌ You already have an active application in progress. Please finish it first or wait for it to expire.', ephemeral=True)
            return

        try:
            start_embed = discord.Embed(
                title='📋 Staff Application Started', 
                description='Welcome to the staff application process!\n\nI\'ll ask you **10 questions** one by one. Please answer them honestly and thoughtfully.\n\n**Type your answer and press Enter** for each question.\n\nYou can type `cancel` at any time to stop the application.', 
                color=0x00AE86
            )
            start_embed.set_footer(text='Question 1 coming up...')
            
            await interaction.user.send(embed=start_embed)
            
            active_applications[user_id] = {
                'user_id': user_id, 
                'guild_id': interaction.guild_id, 
                'answers': [], 
                'current_question': 0, 
                'start_time': datetime.now()
            }

            await interaction.response.send_message('✅ Application started! Check your DMs to continue.', ephemeral=True)

            await asyncio.sleep(2)
            await self.ask_next_question(interaction.client, user_id)

        except discord.Forbidden:
            await interaction.response.send_message('❌ **I couldn\'t send you a DM!**\n\nPlease:\n• Enable DMs from server members\n• Make sure you\'re not blocking the bot\n• Try again after adjusting your privacy settings', ephemeral=True)
        except Exception as e:
            print(f'Error starting application: {e}')
            await interaction.response.send_message('❌ An error occurred while starting your application. Please try again.', ephemeral=True)

    async def ask_next_question(self, bot, user_id):
        if user_id not in active_applications:
            return

        application = active_applications[user_id]
        question_index = application['current_question']
        
        if question_index >= len(QUESTIONS):
            await self.submit_application(bot, user_id)
            return

        try:
            user = bot.get_user(user_id)
            if not user:
                print(f"Could not find user {user_id}")
                return

            color = 0xFF6B6B if question_index >= 8 else 0x4ECDC4
            footer_text = 'Meme Question - Have fun! 😄' if question_index >= 8 else 'Please answer thoughtfully'

            question_embed = discord.Embed(
                title=f'Question {question_index + 1}/{len(QUESTIONS)}', 
                description=QUESTIONS[question_index], 
                color=color
            )
            question_embed.set_footer(text=footer_text)

            await user.send(embed=question_embed)
            print(f"Sent question {question_index + 1} to {user.name}")
            
        except Exception as e:
            print(f'Error sending question: {e}')
            if user_id in active_applications:
                del active_applications[user_id]

    async def submit_application(self, bot, user_id):
        if user_id not in active_applications:
            return

        application = active_applications[user_id]

        try:
            user = bot.get_user(user_id)
            guild = bot.get_guild(application['guild_id'])
            staff_channel = guild.get_channel(STAFF_CHANNEL_ID)

            # Handle username display properly for new username system
            username_display = f"{user.name}"
            if hasattr(user, 'global_name') and user.global_name:
                username_display = f"{user.global_name} (@{user.name})"

            application_embed = discord.Embed(
                title='📋 New Staff Application', 
                description=f'**Applicant:** {user.mention} ({username_display})\n**User ID:** {user.id}\n**Submitted:** <t:{int(datetime.now().timestamp())}:R>', 
                color=0x00AE86
            )
            application_embed.set_thumbnail(url=user.display_avatar.url)

            for answer in application['answers']:
                field_name = f"{answer['question_number']}. {answer['question']}"
                field_value = answer['answer']
                
                if len(field_value) > 1024:
                    field_value = field_value[:1021] + '...'
                
                application_embed.add_field(name=field_name, value=field_value, inline=False)

            view = ReviewView(user_id)
            await staff_channel.send(embed=application_embed, view=view)

            success_embed = discord.Embed(
                title='✅ Application Submitted!', 
                description='Thank you for your application! Our staff team will review it and get back to you soon.\n\nYou\'ll receive a DM when a decision has been made.', 
                color=0x00AE86
            )
            success_embed.set_footer(text='Typical review time: 24-48 hours')

            await user.send(embed=success_embed)

            del active_applications[user_id]
            print(f"Application submitted for {user.name}")

        except Exception as e:
            print(f'Error submitting application: {e}')
            if user_id in active_applications:
                del active_applications[user_id]

class ReviewView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id
    
    @discord.ui.button(label='Approve', style=discord.ButtonStyle.success, emoji='✅', custom_id='approve')
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check for proper permissions
        if not (interaction.user.guild_permissions.manage_guild or 
                any(role.id == STAFF_ROLE_ID for role in interaction.user.roles)):
            await interaction.response.send_message('❌ You don\'t have permission to review applications.', ephemeral=True)
            return

        try:
            applicant = interaction.client.get_user(self.user_id)
            guild = interaction.guild
            
            member = await guild.fetch_member(self.user_id)
            role = guild.get_role(STAFF_ROLE_ID)
            
            if role:
                await member.add_roles(role)

            updated_embed = interaction.message.embeds[0]
            updated_embed.title = '✅ Application APPROVED'
            updated_embed.color = 0x00FF00
            updated_embed.set_footer(text=f'Approved by {interaction.user.name} on {datetime.now().strftime("%Y-%m-%d %H:%M")}')

            await interaction.response.edit_message(embed=updated_embed, view=None)

            approval_embed = discord.Embed(
                title='🎉 Application Approved!', 
                description=f'Congratulations! Your staff application has been **approved**.\n\nYou have been given the staff role and can now access staff channels.\n\nWelcome to the team! 🎊', 
                color=0x00FF00
            )
            approval_embed.set_footer(text=f'Reviewed by {interaction.user.name}')

            await applicant.send(embed=approval_embed)

        except Exception as e:
            print(f'Error handling application approval: {e}')
            await interaction.response.send_message('❌ An error occurred while processing the application.', ephemeral=True)
    
    @discord.ui.button(label='Reject', style=discord.ButtonStyle.danger, emoji='❌', custom_id='reject')
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check for proper permissions
        if not (interaction.user.guild_permissions.manage_guild or 
                any(role.id == STAFF_ROLE_ID for role in interaction.user.roles)):
            await interaction.response.send_message('❌ You don\'t have permission to review applications.', ephemeral=True)
            return

        try:
            applicant = interaction.client.get_user(self.user_id)

            updated_embed = interaction.message.embeds[0]
            updated_embed.title = '❌ Application REJECTED'
            updated_embed.color = 0xFF0000
            updated_embed.set_footer(text=f'Rejected by {interaction.user.name} on {datetime.now().strftime("%Y-%m-%d %H:%M")}')

            await interaction.response.edit_message(embed=updated_embed, view=None)

            rejection_embed = discord.Embed(
                title='❌ Application Status Update', 
                description=f'Thank you for your interest in joining our staff team.\n\nAfter careful review, we\'ve decided not to move forward with your application at this time.\n\nYou\'re welcome to apply again in the future!', 
                color=0xFF6B6B
            )
            rejection_embed.set_footer(text=f'Reviewed by {interaction.user.name}')

            await applicant.send(embed=rejection_embed)

        except Exception as e:
            print(f'Error handling application rejection: {e}')
            await interaction.response.send_message('❌ An error occurred while processing the application.', ephemeral=True)

@tasks.loop(minutes=30)
async def cleanup_expired_applications():
    """Clean up expired applications"""
    now = datetime.now()
    expired_users = []
    
    for user_id, application in active_applications.items():
        if now - application['start_time'] > timedelta(hours=1):
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del active_applications[user_id]
        print(f'Cleaned up expired application for user {user_id}')

async def setup_application_system(bot):
    """Call this in your bot's on_ready event"""
    try:
        # Start cleanup task
        if not cleanup_expired_applications.is_running():
            cleanup_expired_applications.start()
        
        # Add persistent view
        bot.add_view(ApplicationView())
        bot.add_view(ReviewView(0))  # Add with dummy user_id for persistence
        
        # Send the embed
        await setup_application_embed(bot)
        
    except Exception as e:
        print(f"Application system error: {e}")

async def setup_application_embed(bot):
    """Send the application embed to the designated channel"""
    try:
        channel = bot.get_channel(APPLY_CHANNEL_ID)
        if not channel:
            print(f'Channel {APPLY_CHANNEL_ID} not found')
            return

        embed = discord.Embed(
            title='📋 Staff Application', 
            description='Ready to join our amazing staff team?\n\nClick the button below to start your application process. You\'ll receive a private message with questions to fill out.', 
            color=0x00AE86
        )
        embed.add_field(name='📝 Process', value='• Click "Apply Now"\n• Answer questions in DMs\n• Wait for staff review\n• Get notified of decision', inline=True)
        embed.add_field(name='⏱️ Time Required', value='About 5-10 minutes', inline=True)
        embed.add_field(name='📋 Questions', value='10 questions total', inline=True)
        embed.set_footer(text='Make sure your DMs are open!')
        embed.timestamp = datetime.now()

        view = ApplicationView()
        await channel.send(embed=embed, view=view)
        print(f'Application embed sent to #{channel.name}')
        
    except Exception as e:
        print(f'Error sending embed: {e}')

async def handle_application_dm(bot, message):
    """Handle DM responses for applications"""
    if message.author.bot or not isinstance(message.channel, discord.DMChannel):
        return

    user_id = message.author.id
    if user_id not in active_applications:
        return

    application = active_applications[user_id]

    if message.content.lower() == 'cancel':
        del active_applications[user_id]
        cancel_embed = discord.Embed(title='❌ Application Cancelled', description='Your application has been cancelled. You can start a new one anytime!', color=0xFF6B6B)
        await message.reply(embed=cancel_embed)
        return

    # Store the answer
    application['answers'].append({
        'question': QUESTIONS[application['current_question']], 
        'answer': message.content, 
        'question_number': application['current_question'] + 1
    })

    application['current_question'] += 1
    await message.add_reaction('✅')
    
    await asyncio.sleep(1)
    app_view = ApplicationView()
    await app_view.ask_next_question(bot, user_id)

# EVENT HANDLERS
@bot.event
async def on_ready():
    print(f'{bot.user} has logged in!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Set up the application system
    await setup_application_system(bot)
    print('Application system initialized!')

@bot.event
async def on_message(message):
    # Handle application DMs
    await handle_application_dm(bot, message)
    
    # Process other commands
    await bot.process_commands(message)

# OPTIONAL: Add some basic commands
@bot.command(name='ping')
async def ping(ctx):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name='setup_app')
@commands.has_permissions(manage_guild=True)
async def setup_app_command(ctx):
    """Manually set up the application embed (Admin only)"""
    await setup_application_embed(bot)
    await ctx.send('✅ Application embed set up!')

# Staff Application System - Add this to your existing bot code

# Configuration for staff applications
STAFF_APPLY_CHANNEL_ID = 1379879557984944270  # Channel for apply embed
STAFF_RESULTS_CHANNEL_ID = 1380229490617352391  # Channel for application results
STAFF_ROLE_ID = 1380228782606127265  # Role to give when accepted

# Store ongoing applications
active_applications = {}

# Staff application questions
STAFF_QUESTIONS = [
    "What is your age?",
    "What timezone are you in?",
    "How many hours per day can you dedicate to moderating?",
    "Do you have any previous moderation experience? If yes, please describe.",
    "Why do you want to become a staff member?",
    "How would you handle a situation where two members are arguing?",
    "What would you do if you caught a friend breaking the rules?",
    "Do you have any other commitments that might affect your activity?",
    "Is there anything else you'd like us to know about you?"
]

class StaffApplicationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='📝 Apply for Staff', style=discord.ButtonStyle.primary, custom_id='apply_staff')
    async def apply_staff(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        # Check if user already has an active application
        if user_id in active_applications:
            await interaction.response.send_message("❌ You already have an active staff application! Please complete or cancel your current application first.", ephemeral=True)
            return
        
        # Try to send a DM to check if DMs are open
        try:
            dm_channel = await interaction.user.create_dm()
            test_embed = discord.Embed(
                title="📝 Staff Application Started",
                description="Your staff application has been started! Please answer the following questions honestly and thoroughly.",
                color=discord.Color.blue()
            )
            test_embed.set_footer(text="You have 10 minutes to answer each question.")
            await dm_channel.send(embed=test_embed)
            
            # Initialize application data
            active_applications[user_id] = {
                'user': interaction.user,
                'answers': [],
                'current_question': 0,
                'guild_id': interaction.guild.id,
                'start_time': discord.utils.utcnow()
            }
            
            await interaction.response.send_message("✅ Staff application started! Check your DMs to begin answering questions.", ephemeral=True)
            
            # Start the application process
            await ask_next_question(user_id)
            
        except discord.Forbidden:
            await interaction.response.send_message("❌ I cannot send you a DM! Please enable DMs from server members and try again.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ An error occurred while starting your application: {str(e)}", ephemeral=True)

async def ask_next_question(user_id):
    """Ask the next question in the staff application"""
    if user_id not in active_applications:
        return
    
    app_data = active_applications[user_id]
    question_num = app_data['current_question']
    
    if question_num >= len(STAFF_QUESTIONS):
        # Application complete
        await complete_application(user_id)
        return
    
    user = app_data['user']
    try:
        dm_channel = await user.create_dm()
        
        embed = discord.Embed(
            title=f"Question {question_num + 1}/{len(STAFF_QUESTIONS)}",
            description=STAFF_QUESTIONS[question_num],
            color=discord.Color.blue()
        )
        embed.set_footer(text="Please respond with your answer. You have 10 minutes to respond.")
        
        await dm_channel.send(embed=embed)
        
        # Set up timeout for response
        asyncio.create_task(question_timeout(user_id, question_num))
        
    except discord.Forbidden:
        # User closed DMs during application
        if user_id in active_applications:
            del active_applications[user_id]
    except Exception as e:
        print(f"Error asking question to {user_id}: {e}")
        if user_id in active_applications:
            del active_applications[user_id]

async def question_timeout(user_id, question_num):
    """Handle timeout for application questions"""
    await asyncio.sleep(600)  # 10 minutes
    
    if user_id in active_applications and active_applications[user_id]['current_question'] == question_num:
        user = active_applications[user_id]['user']
        try:
            dm_channel = await user.create_dm()
            embed = discord.Embed(
                title="❌ Application Timed Out",
                description="Your staff application has been cancelled due to inactivity. You can start a new application anytime.",
                color=discord.Color.red()
            )
            await dm_channel.send(embed=embed)
        except:
            pass
        
        del active_applications[user_id]

async def complete_application(user_id):
    """Complete the staff application and send results"""
    if user_id not in active_applications:
        return
    
    app_data = active_applications[user_id]
    user = app_data['user']
    guild = bot.get_guild(app_data['guild_id'])
    
    if not guild:
        del active_applications[user_id]
        return
    
    try:
        # Send completion message to user
        dm_channel = await user.create_dm()
        completion_embed = discord.Embed(
            title="✅ Application Submitted!",
            description="Thank you for submitting your staff application! Our team will review it and get back to you soon.",
            color=discord.Color.green()
        )
        await dm_channel.send(embed=completion_embed)
        
        # Send application to results channel
        results_channel = guild.get_channel(STAFF_RESULTS_CHANNEL_ID)
        if results_channel:
            app_embed = discord.Embed(
                title="📝 New Staff Application",
                description=f"**Applicant:** {user.mention} ({user.name}#{user.discriminator})\n**User ID:** {user.id}",
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow()
            )
            
            app_embed.set_thumbnail(url=user.avatar.url if user.avatar else user.default_avatar.url)
            
            # Add questions and answers
            for i, (question, answer) in enumerate(zip(STAFF_QUESTIONS, app_data['answers'])):
                app_embed.add_field(
                    name=f"Q{i+1}: {question}",
                    value=answer[:1024] if len(answer) <= 1024 else answer[:1021] + "...",
                    inline=False
                )
            
            app_embed.set_footer(text="Use the buttons below to accept or deny this application")
            
            # Create accept/deny view
            decision_view = StaffDecisionView(user_id)
            await results_channel.send(embed=app_embed, view=decision_view)
            
            # Log application submission
            await send_log(
                guild,
                "Staff Application Submitted",
                f"New staff application submitted by {user.mention}",
                color=discord.Color.blue(),
                user=user,
                additional_fields=[
                    {"name": "Application Channel", "value": results_channel.mention, "inline": True},
                    {"name": "Questions Answered", "value": str(len(app_data['answers'])), "inline": True}
                ]
            )
    
    except Exception as e:
        print(f"Error completing application for {user_id}: {e}")
    
    # Clean up
    del active_applications[user_id]

class StaffDecisionView(discord.ui.View):
    def __init__(self, applicant_id):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
    
    @discord.ui.button(label='✅ Accept', style=discord.ButtonStyle.success, custom_id='accept_staff')
    async def accept_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has permission to make decisions
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to make staff decisions!", ephemeral=True)
            return
        
        guild = interaction.guild
        applicant = guild.get_member(self.applicant_id)
        
        if not applicant:
            await interaction.response.send_message("❌ Applicant is no longer in the server!", ephemeral=True)
            return
        
        try:
            # Give staff role
            staff_role = guild.get_role(STAFF_ROLE_ID)
            if staff_role:
                await applicant.add_roles(staff_role, reason=f"Staff application accepted by {interaction.user}")
            
            # Send acceptance DM
            try:
                dm_channel = await applicant.create_dm()
                accept_embed = discord.Embed(
                    title="🎉 Staff Application Accepted!",
                    description=f"Congratulations! Your staff application for **{guild.name}** has been accepted!\nWelcome to the team!",
                    color=discord.Color.green()
                )
                await dm_channel.send(embed=accept_embed)
            except:
                pass  # User has DMs disabled
            
            # Update the embed
            embed = discord.Embed(
                title="✅ Application Accepted",
                description=f"**Applicant:** {applicant.mention}\n**Accepted by:** {interaction.user.mention}\n**Status:** Accepted and role assigned",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            
            await interaction.response.edit_message(embed=embed, view=None)
            
            # Log acceptance
            await send_log(
                guild,
                "Staff Application Accepted",
                f"Staff application accepted for {applicant.mention}",
                color=discord.Color.green(),
                user=interaction.user,
                additional_fields=[
                    {"name": "Applicant", "value": applicant.mention, "inline": True},
                    {"name": "Accepted By", "value": interaction.user.mention, "inline": True},
                    {"name": "Role Assigned", "value": staff_role.mention if staff_role else "Role not found", "inline": True}
                ]
            )
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error accepting application: {str(e)}", ephemeral=True)
    
    @discord.ui.button(label='❌ Deny', style=discord.ButtonStyle.danger, custom_id='deny_staff')
    async def deny_application(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Check if user has permission to make decisions
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ You don't have permission to make staff decisions!", ephemeral=True)
            return
        
        guild = interaction.guild
        applicant = guild.get_member(self.applicant_id)
        
        if applicant:
            # Send denial DM
            try:
                dm_channel = await applicant.create_dm()
                deny_embed = discord.Embed(
                    title="❌ Staff Application Denied",
                    description=f"Thank you for your interest in becoming a staff member for **{guild.name}**.\n\nUnfortunately, your application has been denied at this time. You may reapply in the future.",
                    color=discord.Color.red()
                )
                await dm_channel.send(embed=deny_embed)
            except:
                pass  # User has DMs disabled
        
        # Update the embed
        embed = discord.Embed(
            title="❌ Application Denied",
            description=f"**Applicant:** {applicant.mention if applicant else 'User left server'}\n**Denied by:** {interaction.user.mention}\n**Status:** Denied",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Log denial
        await send_log(
            guild,
            "Staff Application Denied",
            f"Staff application denied for {applicant.mention if applicant else 'User who left server'}",
            color=discord.Color.red(),
            user=interaction.user,
            additional_fields=[
                {"name": "Applicant", "value": applicant.mention if applicant else "User left server", "inline": True},
                {"name": "Denied By", "value": interaction.user.mention, "inline": True}
            ]
        )

@bot.event
async def on_message(message):
    """Handle DM responses for staff applications"""
    # Don't respond to bots
    if message.author.bot:
        return
    
    # Check if it's a DM and user has active application
    if isinstance(message.channel, discord.DMChannel) and message.author.id in active_applications:
        user_id = message.author.id
        app_data = active_applications[user_id]
        
        # Store the answer
        app_data['answers'].append(message.content)
        app_data['current_question'] += 1
        
        # Ask next question or complete application
        await ask_next_question(user_id)
        return
    
    # Process other messages and commands normally
    await bot.process_commands(message)

# Setup staff application panel
async def setup_staff_panel(guild):
    """Set up the staff application panel"""
    staff_channel = guild.get_channel(STAFF_APPLY_CHANNEL_ID)
    
    if staff_channel:
        try:
            # Check if panel already exists
            async for message in staff_channel.history(limit=50):
                if message.author == bot.user and "📝 Apply for Staff" in str(message.content):
                    return  # Panel already exists
            
            # Create staff application embed
            embed = discord.Embed(
                title="📝 Staff Applications",
                description="Interested in becoming a staff member? Click the button below to start your application!\n\n**Requirements:**\n• Must be active in the server\n• Must have DMs enabled\n• Must be mature and responsible\n• Must follow all server rules\n\n**Application Process:**\n• Click the button to start\n• Answer questions in your DMs\n• Wait for staff review\n• Receive decision via DM",
                color=discord.Color.blue()
            )
            embed.set_footer(text="Make sure your DMs are open before applying!")
            
            # Create view with button
            view = StaffApplicationView()
            await staff_channel.send(embed=embed, view=view)
            
        except Exception as e:
            print(f"Failed to set up staff application panel: {e}")

# Add this to your existing on_ready event (modify your existing on_ready function)
@bot.event
async def on_ready():
    """Bot startup event - MODIFY YOUR EXISTING ON_READY TO INCLUDE THIS"""
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Log bot startup
    for guild in bot.guilds:
        await send_log(
            guild,
            "Bot Started",
            f"Bot {bot.user.name} has come online",
            color=discord.Color.blue(),
            additional_fields=[
                {"name": "Bot ID", "value": bot.user.id, "inline": True},
                {"name": "Guilds", "value": len(bot.guilds), "inline": True}
            ]
        )
        
        # Set up ticket panel
        await setup_ticket_panel(guild)
        
        # Set up staff application panel
        await setup_staff_panel(guild)
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

#start
if __name__ == "__main__":
    # Get token from environment variable or user input
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    
    if not bot_token:
        bot_token = input("Enter your Discord bot token: ").strip()
        
        if not bot_token:
            print("No token provided. Exiting...")
            exit(1)
    
    try:
        # Run the bot
        bot.run(bot_token)
    except discord.LoginFailure:
        print("Invalid bot token provided!")
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Bot has been shut down.")