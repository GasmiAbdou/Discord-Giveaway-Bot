import discord
from discord.ext import commands, tasks
import asyncio
import random
import datetime
import json
import os
import re
from math import ceil
from discord import Embed, SelectOption, Interaction
from discord.ui import Select, View, Modal, TextInput
from helper import *
from dotenv import load_dotenv

load_dotenv()


DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

giveaway_settings = load_giveaway_settings()


class GiveawaySettingsView(View):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.add_item(self.image_select())
        self.add_item(self.thumbnail_select())
        self.add_item(self.color_select())
        self.add_item(self.emoji_button())
        self.add_item(self.footer_button())

    def image_select(self):
        select = Select(
            placeholder="Select image option",
            options=[
                SelectOption(label="Default", value="default"),
                SelectOption(label="Custom", value="custom"),
            ]
        )
        select.callback = self.image_callback
        return select

    def thumbnail_select(self):
        select = Select(
            placeholder="Select thumbnail option",
            options=[
                SelectOption(label="Default", value="default"),
                SelectOption(label="Custom", value="custom"),
            ]
        )
        select.callback = self.thumbnail_callback
        return select

    def color_select(self):
        select = Select(
            placeholder="Select color scheme",
            options=[
                SelectOption(label="Default", value="default"),
                SelectOption(label="Custom", value="custom"),
            ]
        )
        select.callback = self.color_callback
        return select

    def emoji_button(self):
        button = discord.ui.Button(label="Set Custom Emoji", style=discord.ButtonStyle.primary)
        button.callback = self.emoji_callback
        return button


    def footer_button(self):
        button = discord.ui.Button(label="Set Custom Footer", style=discord.ButtonStyle.primary)
        button.callback = self.footer_callback
        return button

    async def image_callback(self, interaction: Interaction):
        if interaction.data['values'][0] == "custom":
            await interaction.response.send_modal(ImageURLModal(self))  # Use modal for image URL
        else:
            giveaway_settings.setdefault(str(interaction.guild_id), {}).pop("image", None)
            save_giveaway_settings(giveaway_settings)
            await interaction.response.send_message("Image set to default.", ephemeral=True)
        await self.update_settings_embed(interaction)

    async def thumbnail_callback(self, interaction: Interaction):
        if interaction.data['values'][0] == "custom":
            await interaction.response.send_modal(ThumbnailURLModal(self))  # Use modal for thumbnail URL
        else:
            giveaway_settings.setdefault(str(interaction.guild_id), {}).pop("thumbnail", None)
            save_giveaway_settings(giveaway_settings)
            await interaction.response.send_message("Thumbnail set to default.", ephemeral=True)
        await self.update_settings_embed(interaction)

    async def color_callback(self, interaction: Interaction):
        if interaction.data['values'][0] == "custom":
            await interaction.response.send_modal(ColorSchemeModal(self))
        else:
            giveaway_settings.setdefault(str(interaction.guild_id), {}).pop("primary_color", None)
            giveaway_settings.setdefault(str(interaction.guild_id), {}).pop("secondary_color", None)
            save_giveaway_settings(giveaway_settings)
            await interaction.response.send_message("Color scheme set to default.", ephemeral=True)
            await self.update_settings_embed(interaction)

    async def emoji_callback(self, interaction: Interaction):
        await interaction.response.send_modal(EmojiModal(self))


    async def footer_callback(self, interaction: Interaction):
        await interaction.response.send_modal(FooterModal(self))

    async def update_settings_embed(self, interaction: Interaction):
        embed = create_settings_embed(interaction.guild)
        await interaction.message.edit(embed=embed)
        #await interaction.followup.send("Settings updated successfully!", ephemeral=True)


class ImageURLModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Image URL")
        self.view = view
        self.image_url = TextInput(label="Image URL", placeholder="Enter the image URL")
        self.add_item(self.image_url)

    async def on_submit(self, interaction: Interaction):
        image_url = self.image_url.value
        giveaway_settings.setdefault(str(interaction.guild_id), {})["image"] = image_url
        save_giveaway_settings(giveaway_settings)
        await self.view.update_settings_embed(interaction)

class ThumbnailURLModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Thumbnail URL")
        self.view = view
        self.thumbnail_url = TextInput(label="Thumbnail URL", placeholder="Enter the thumbnail URL")
        self.add_item(self.thumbnail_url)

    async def on_submit(self, interaction: Interaction):
        thumbnail_url = self.thumbnail_url.value
        giveaway_settings.setdefault(str(interaction.guild_id), {})["thumbnail"] = thumbnail_url
        save_giveaway_settings(giveaway_settings)
        await self.view.update_settings_embed(interaction)


class ColorSchemeModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Color Scheme")
        self.view = view
        self.primary_color = TextInput(label="Primary Color (Hex)", placeholder="e.g., #FF0000")
        self.secondary_color = TextInput(label="Secondary Color (Hex)", placeholder="e.g., #00FF00")
        self.add_item(self.primary_color)
        self.add_item(self.secondary_color)

    async def on_submit(self, interaction: Interaction):
        primary = self.primary_color.value.strip('#')
        secondary = self.secondary_color.value.strip('#')
        if len(primary) != 6 or len(secondary) != 6:
            await interaction.response.send_message("Invalid color format. Please use 6-digit hex codes.", ephemeral=True)
            return
        giveaway_settings.setdefault(str(interaction.guild_id), {})["primary_color"] = primary
        giveaway_settings[str(interaction.guild_id)]["secondary_color"] = secondary
        save_giveaway_settings(giveaway_settings)
        await self.view.update_settings_embed(interaction)

class EmojiModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Emoji")
        self.view = view
        self.emoji = TextInput(label="Custom Emoji", placeholder="Enter an emoji or custom Discord emoji", max_length=2)
        self.add_item(self.emoji)

    async def on_submit(self, interaction: Interaction):
        emoji = self.emoji.value.strip()
        old_emoji = giveaway_settings.get(str(interaction.guild_id), {}).get("button_emoji", "🎉")
        
        # Check if it's a custom Discord emoji
        if emoji.startswith('<') and emoji.endswith('>'):
            # It's a custom emoji, so we'll keep it as is
            new_emoji = emoji
        else:
            # It's a Unicode emoji, so we'll ensure it's a single character
            new_emoji = emoji[:2]  # Take up to two characters to support some composite emojis
        
        giveaway_settings.setdefault(str(interaction.guild_id), {})["button_emoji"] = new_emoji
        save_giveaway_settings(giveaway_settings)
        
        await interaction.response.send_message(f"Emoji updated from {old_emoji} to {new_emoji}", ephemeral=True)
        await self.view.update_settings_embed(interaction)

class FooterModal(Modal):
    def __init__(self, view):
        super().__init__(title="Set Custom Footer")
        self.view = view
        max_length = 2048 - 1  # Discord embed footer limit minus 1
        self.footer = TextInput(label="Custom Footer Text", style=discord.TextStyle.paragraph, max_length=max_length)
        self.add_item(self.footer)

    async def on_submit(self, interaction: Interaction):
        footer_text = self.footer.value
        giveaway_settings.setdefault(str(interaction.guild_id), {})["footer_text"] = footer_text
        save_giveaway_settings(giveaway_settings)
        await self.view.update_settings_embed(interaction)
        await interaction.response.send_message(f"Submitted footer text to **{interaction.guild.name}**", ephemeral=True)  # Confirmation message

def create_settings_embed(guild):
    settings = giveaway_settings.get(str(guild.id), {})
    embed = Embed(title="Giveaway Settings", color=int(settings.get("primary_color", "00ff00"), 16))
    embed.add_field(name="Image", value="Custom" if "image" in settings else "Default", inline=True)
    embed.add_field(name="Thumbnail", value="Custom" if "thumbnail" in settings else "Default", inline=True)
    embed.add_field(name="Color Scheme", value="Custom" if "primary_color" in settings else "Default", inline=True)
    embed.add_field(name="Button Emoji", value=settings.get("button_emoji", "🎉"), inline=True)
    embed.add_field(name="Custom Footer", value="Set" if "footer_text" in settings else "Default", inline=True)
    
    if "image" in settings:
        embed.set_image(url=settings["image"])
    if "thumbnail" in settings:
        embed.set_thumbnail(url=settings["thumbnail"])
    
    footer_text = settings.get("footer_text", f"Server ID: {guild.id}")
    embed.set_footer(text=footer_text)
    return embed



class Giveaway:
    def __init__(self, channel_id, prize, duration, host_id, winners=1, role_requirement=None, server_requirement=None, server_invite=None, notes=None, message_id=None, end_time=None, entry_limit=None):
        self.channel_id = channel_id
        self.prize = prize
        self.duration = max(duration, 60)  # Ensure minimum duration of 1 minute
        self.host_id = host_id
        self.winners = winners
        self.role_requirement = role_requirement
        self.server_requirement = server_requirement
        self.server_invite = server_invite
        self.notes = notes or ""
        self.participants = set()
        self.message_id = message_id
        self.end_time = end_time or (datetime.datetime.now() + datetime.timedelta(seconds=self.duration)).timestamp()
        self.ended = False
        self.entry_limit = entry_limit  # Added entry_limit attribute

    def to_dict(self):
        return {
            "channel_id": self.channel_id,
            "prize": self.prize,
            "duration": self.duration,
            "host_id": self.host_id,
            "winners": self.winners,
            "role_requirement": self.role_requirement,
            "server_requirement": self.server_requirement,
            "server_invite": self.server_invite,
            "notes": self.notes,
            "participants": list(self.participants),
            "message_id": self.message_id,
            "end_time": self.end_time,
            "ended": self.ended,
            "entry_limit": self.entry_limit  # Added entry_limit to the dictionary
        }

    @classmethod
    def from_dict(cls, data):
        giveaway = cls(
            data["channel_id"],
            data["prize"],
            data["duration"],
            data["host_id"],
            data["winners"],
            data["role_requirement"],
            data["server_requirement"],
            data["server_invite"],
            data["notes"],
            data["message_id"],
            data["end_time"]
        )
        giveaway.participants = set(data["participants"])
        giveaway.ended = data["ended"]
        giveaway.entry_limit = data.get("entry_limit")  # Set the entry_limit attribute
        return giveaway



class GiveawayModal(discord.ui.Modal, title="Create a Giveaway"):
    prize = discord.ui.TextInput(label="Prize", placeholder="Enter the giveaway prize")
    duration = discord.ui.TextInput(label="Duration", placeholder="Enter the duration (e.g., 1h 30m, 2d)")
    winners = discord.ui.TextInput(label="Number of Winners", placeholder="Enter the number of winners")
    notes = discord.ui.TextInput(label="Notes (optional)", placeholder="Enter any additional notes", style=discord.TextStyle.long, required=False)

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx

    async def on_submit(self, interaction: discord.Interaction):
        try:
            duration_seconds = max(parse_duration(self.duration.value), 60)  # Ensure minimum duration of 1 minute
            winners = int(self.winners.value)

            if winners <= 0:
                raise ValueError("Number of winners must be positive")

            # Store the giveaway data temporarily
            interaction.client.temp_giveaway_data = {
                "prize": self.prize.value,
                "duration": duration_seconds,
                "winners": winners,
                "notes": self.notes.value,
                "channel_id": interaction.channel_id,
                "host_id": interaction.user.id,
            }

            # Create a select menu for requirements
            select = discord.ui.Select(
                placeholder="Add requirements or limits?",  # Updated placeholder
                options=[
                    discord.SelectOption(label="No requirements", value="none"),
                    discord.SelectOption(label="Role requirement", value="role"),
                    discord.SelectOption(label="Server requirement", value="server"),
                    discord.SelectOption(label="Entry Limit", value="limit"),  # New option
                ]
            )

            async def select_callback(interaction: discord.Interaction):
                if select.values[0] == "none":
                    await update_confirmation_message(interaction, None, None, None)  # Pass None for entry_limit
                elif select.values[0] == "role":
                    await interaction.response.send_modal(RoleRequirementModal())
                elif select.values[0] == "server":
                    await interaction.response.send_modal(ServerRequirementModal())
                elif select.values[0] == "limit":  # Handle entry limit
                    await interaction.response.send_modal(EntryLimitModal())

            select.callback = select_callback
            view = discord.ui.View()
            view.add_item(select)

            # Create and send the initial confirmation message
            embed = create_confirmation_embed(interaction.client.temp_giveaway_data, None, None, None)  # Pass None for entry_limit
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

        except ValueError as e:
            await interaction.response.send_message(f"Invalid input: {str(e)}. Giveaway creation cancelled.", ephemeral=True)

class RoleRequirementModal(discord.ui.Modal, title="Role Requirement"):
    role = discord.ui.TextInput(label="Role", placeholder="Enter role name or ID")

    async def on_submit(self, interaction: discord.Interaction):
        role_requirement = await get_role(interaction, self.role.value)
        if role_requirement:
            await update_confirmation_message(interaction, role_requirement, None)
        else:
            await interaction.response.send_message("Couldn't find the specified role. Please try again.", ephemeral=True)

class ServerRequirementModal(discord.ui.Modal, title="Server Requirement"):
    server = discord.ui.TextInput(label="Server ID", placeholder="Enter server ID")

    async def on_submit(self, interaction: discord.Interaction):
        server_requirement, server_invite = await get_server(interaction, self.server.value)
        if server_requirement:
            interaction.client.temp_giveaway_data["server_invite"] = server_invite
            await update_confirmation_message(interaction, None, server_requirement)
        else:
            await interaction.response.send_message("I'm not in the specified server or couldn't create an invite. Please try again.", ephemeral=True)

class EntryLimitModal(discord.ui.Modal, title="Entry Limit"):
    limit = discord.ui.TextInput(label="Entry Limit", placeholder="Enter the maximum number of entries")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            entry_limit = int(self.limit.value)
            if entry_limit <= 0:
                raise ValueError("Entry limit must be a positive number.")
            await update_confirmation_message(interaction, None, None, entry_limit)
        except ValueError as e:
            await interaction.response.send_message(f"Invalid input: {e}", ephemeral=True)

def create_confirmation_embed(giveaway_data, role_requirement, server_requirement, entry_limit):
    embed = discord.Embed(title="Giveaway Confirmation", color=0x00ff00)
    embed.add_field(name="Prize", value=giveaway_data["prize"], inline=False)
    embed.add_field(name="Duration", value=f"{giveaway_data['duration']} seconds", inline=False)
    embed.add_field(name="Winners", value=str(giveaway_data["winners"]), inline=False)
    
    role_status = "✅" if role_requirement else "❌"
    server_status = "✅" if server_requirement else "❌"
    limit_status = f"✅ ({entry_limit})" if entry_limit else "❌"
    embed.description = f"**Requirements & Limits:**\n* Role requirement: {role_status}\n* Server requirement: {server_status}\n* Entry Limit: {limit_status}"
    
    if giveaway_data.get("notes"):
        embed.add_field(name="Notes", value=giveaway_data["notes"], inline=False)
    
    return embed

async def update_confirmation_message(interaction: discord.Interaction, role_requirement, server_requirement, entry_limit):
    giveaway_data = interaction.client.temp_giveaway_data
    if role_requirement:
        giveaway_data["role_requirement"] = role_requirement
    if server_requirement:
        giveaway_data["server_requirement"] = server_requirement
    
    embed = create_confirmation_embed(giveaway_data, giveaway_data.get("role_requirement"), giveaway_data.get("server_requirement"), entry_limit)  # Pass entry_limit
    
    view = discord.ui.View()
    confirm_button = discord.ui.Button(label="Confirm and Launch Giveaway", style=discord.ButtonStyle.green)
    
    async def confirm_callback(interaction: discord.Interaction):
        await create_giveaway(interaction, giveaway_data.get("role_requirement"), giveaway_data.get("server_requirement"), giveaway_data.get("server_invite"))
    
    confirm_button.callback = confirm_callback
    view.add_item(confirm_button)
    
    # Add the requirements/limits select menu back to the view
    select = discord.ui.Select(
        placeholder="Update requirements or limits?",  # Updated placeholder
        options=[
            discord.SelectOption(label="No requirements", value="none"),
            discord.SelectOption(label="Role requirement", value="role"),
            discord.SelectOption(label="Server requirement", value="server"),
            discord.SelectOption(label="Entry Limit", value="limit"),  # New option
        ]
    )

    async def select_callback(interaction: discord.Interaction):
        if select.values[0] == "none":
            await update_confirmation_message(interaction, None, None, None)  # Pass None for entry_limit
        elif select.values[0] == "role":
            await interaction.response.send_modal(RoleRequirementModal())
        elif select.values[0] == "server":
            await interaction.response.send_modal(ServerRequirementModal())
        elif select.values[0] == "limit":  # Handle entry limit
            await interaction.response.send_modal(EntryLimitModal())
    
    select.callback = select_callback
    view.add_item(select)
    
    await interaction.response.edit_message(embed=embed, view=view)

async def create_giveaway(interaction: discord.Interaction, role_requirement, server_requirement, server_invite):
    giveaway_data = interaction.client.temp_giveaway_data
    giveaway_data["role_requirement"] = role_requirement
    giveaway_data["server_requirement"] = server_requirement
    giveaway_data["server_invite"] = server_invite

    giveaway = Giveaway(**giveaway_data)
    giveaway_id = f"{interaction.channel_id}-{interaction.id}"
    active_giveaways[giveaway_id] = giveaway

    settings = giveaway_settings.get(str(interaction.guild_id), {})
    primary_color = int(settings.get("primary_color", "00ff00"), 16)
    secondary_color = int(settings.get("secondary_color", "ff0000"), 16)

    embed = discord.Embed(title="🎉 Giveaway Time! 🎉", color=primary_color)
    embed.description = f"**Prize: {giveaway.prize}**"

    # Main giveaway info (non-inline)
    embed.add_field(name="Host", value=f"<@{giveaway.host_id}>", inline=False)
    embed.add_field(name="Duration", value=f"Ends <t:{int(giveaway.end_time)}:R>", inline=False)

    # Compact info (inline)
    embed.add_field(name="Winners", value=str(giveaway.winners), inline=True)
    embed.add_field(name="Entries", value="0", inline=True)

    # Requirements (if any, non-inline)
    requirements = []
    if giveaway.role_requirement:
        role = interaction.guild.get_role(giveaway.role_requirement)
        requirements.append(f"Role: {role.name}")
    if giveaway.server_requirement:
        server = interaction.client.get_guild(giveaway.server_requirement)
        if server and giveaway.server_invite:
            requirements.append(f"Server: [{server.name}]({giveaway.server_invite})")
        elif server:
            requirements.append(f"Server: {server.name} (Invite unavailable)")
    
    if requirements:
        embed.add_field(name="Requirements", value="\n".join(requirements), inline=False)

    # Notes (if any, non-inline)
    if giveaway.notes:
        embed.add_field(name="Notes", value=giveaway.notes, inline=False)

    footer_text = settings.get("footer_text", "Click the button below to enter!")
    embed.set_footer(text=footer_text)

    # Apply custom settings
    if "image" in settings:
        embed.set_image(url=settings["image"])
    if "thumbnail" in settings:
        embed.set_thumbnail(url=settings["thumbnail"])

    view = GiveawayView(giveaway_id)
    
    # Update the button with custom emoji if set
    button_emoji = settings.get("button_emoji", "🎉")
    for item in view.children:
        if isinstance(item, discord.ui.Button) and item.custom_id == "enter_giveaway":
            item.emoji = button_emoji
            break

    message = await interaction.channel.send(embed=embed, view=view)
    giveaway.message_id = message.id
    save_giveaways()

    await interaction.response.send_message("Giveaway created successfully!", ephemeral=True)

class ParticipantsPaginator(discord.ui.View):
    def __init__(self, participants, per_page=10):
        super().__init__(timeout=60)
        self.participants = list(participants)
        self.per_page = per_page
        self.current_page = 1
        self.total_pages = ceil(len(self.participants) / self.per_page)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.gray, disabled=True)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = max(1, self.current_page - 1)
        await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page = min(self.total_pages, self.current_page + 1)
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        self.previous_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == self.total_pages

        start_idx = (self.current_page - 1) * self.per_page
        end_idx = start_idx + self.per_page
        current_participants = self.participants[start_idx:end_idx]

        embed = discord.Embed(title="Giveaway Participants", color=0x00ff00)
        embed.description = "\n".join(f"<@{participant}>" for participant in current_participants)
        embed.set_footer(text=f"Page {self.current_page}/{self.total_pages}")

        await interaction.response.edit_message(embed=embed, view=self)


class GiveawayView(discord.ui.View):
    def __init__(self, giveaway_id):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id

    @discord.ui.button(label="Enter Giveaway", style=discord.ButtonStyle.green, custom_id="enter_giveaway")
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaway = active_giveaways.get(self.giveaway_id)
        if not giveaway or giveaway.ended:
            await interaction.response.send_message("This giveaway has ended.", ephemeral=True)
            return

        settings = giveaway_settings.get(str(interaction.guild_id), {})
        button_emoji = settings.get("button_emoji", "🎉")
        button.emoji = button_emoji

        if interaction.user.id in giveaway.participants:
            await interaction.response.send_message("You've already entered this giveaway!", ephemeral=True)
            return

        if giveaway.role_requirement:
            role = interaction.guild.get_role(giveaway.role_requirement)
            if role not in interaction.user.roles:
                await interaction.response.send_message(f"You need the {role.name} role to enter this giveaway!", ephemeral=True)
                return

        if giveaway.server_requirement:
            required_server = interaction.client.get_guild(giveaway.server_requirement)
            if not required_server:
                await interaction.response.send_message("I couldn't verify the server requirement. Please contact the giveaway host.", ephemeral=True)
                return
            if interaction.user not in required_server.members:
                if giveaway.server_invite:
                    await interaction.response.send_message(f"You need to be in the required server to enter this giveaway! Join here: {giveaway.server_invite}", ephemeral=True)
                else:
                    await interaction.response.send_message(f"You need to be in the required server to enter this giveaway!", ephemeral=True)
                return
        if giveaway.entry_limit and len(giveaway.participants) >= giveaway.entry_limit:
            await interaction.response.send_message("This giveaway has reached its entry limit.", ephemeral=True)
            return

        giveaway.participants.add(interaction.user.id)
        save_giveaways()
        await interaction.response.send_message("You've successfully entered the giveaway!", ephemeral=True)
        
        # Update the giveaway message with new entry count
        channel = interaction.client.get_channel(giveaway.channel_id)
        message = await channel.fetch_message(giveaway.message_id)
        embed = message.embeds[0]
        
        for i, field in enumerate(embed.fields):
            if field.name == "Entries":
                embed.set_field_at(i, name="Entries", value=str(len(giveaway.participants)), inline=True)
                break

        await message.edit(embed=embed)

    @discord.ui.button(label="View Participants", style=discord.ButtonStyle.blurple, custom_id="view_participants")
    async def view_participants(self, interaction: discord.Interaction, button: discord.ui.Button):
        giveaway = active_giveaways.get(self.giveaway_id)
        if not giveaway:
            await interaction.response.send_message("This giveaway no longer exists.", ephemeral=True)
            return

        if not giveaway.participants:
            await interaction.response.send_message("No one has entered this giveaway yet.", ephemeral=True)
            return

        paginator = ParticipantsPaginator(giveaway.participants)
        
        # Create initial embed
        embed = discord.Embed(title="Giveaway Participants", color=0x00ff00)
        embed.description = "\n".join(f"<@{participant}>" for participant in list(giveaway.participants)[:paginator.per_page])
        embed.set_footer(text=f"Page 1/{paginator.total_pages}")

        # Send the initial message with the paginator view
        await interaction.response.send_message(embed=embed, view=paginator, ephemeral=True)



@bot.hybrid_command(name="giveaway", description="Start a new giveaway")
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx):
    modal = GiveawayModal(ctx)
    await ctx.interaction.response.send_modal(modal)

def parse_duration(duration_str):
    total_seconds = 0
    parts = re.findall(r'(\d+)([dhms])', duration_str.lower())
    for value, unit in parts:
        value = int(value)
        if unit == 'd':
            total_seconds += value * 86400
        elif unit == 'h':
            total_seconds += value * 3600
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 's':
            total_seconds += value
    if total_seconds == 0:
        raise ValueError("Invalid duration format")
    return max(total_seconds, 60)  # Ensure minimum duration of 1 minute

@bot.hybrid_command(name="reroll", description="Reroll the winner(s) of the last giveaway")
@commands.has_permissions(manage_messages=True)
async def reroll(ctx):
    channel_giveaways = [g for g in active_giveaways.values() if g.channel_id == ctx.channel.id and g.ended]
    if not channel_giveaways:
        await ctx.send("There are no ended giveaways to reroll in this channel.")
        return

    giveaway = max(channel_giveaways, key=lambda g: g.end_time)
    if not giveaway.participants:
        await ctx.send("No one participated in the giveaway. 😢")
        return

    new_winners = random.sample(list(giveaway.participants), min(giveaway.winners, len(giveaway.participants)))
    winner_mentions = [f"<@{winner}>" for winner in new_winners]

    embed = discord.Embed(title="🎉 Giveaway Rerolled! 🎉", color=0xff00ff)
    embed.add_field(name="Prize", value=giveaway.prize, inline=False)
    embed.add_field(name="New Winners", value="\n".join(winner_mentions), inline=False)
    embed.set_footer(text=f"Hosted by <@{giveaway.host_id}>")

    await ctx.send(embed=embed)
    await ctx.send(f"Congratulations, {', '.join(winner_mentions)}! You're the new winners of the giveaway for {giveaway.prize}!")

@bot.hybrid_command(name="cancel", description="Cancel the current giveaway")
@commands.has_permissions(manage_messages=True)
async def cancel(ctx):
    channel_giveaways = [gid for gid, g in active_giveaways.items() if g.channel_id == ctx.channel.id and not g.ended]
    if not channel_giveaways:
        await ctx.send("There's no active giveaway to cancel in this channel.")
        return

    giveaway_id = channel_giveaways[0]
    giveaway = active_giveaways[giveaway_id]
    del active_giveaways[giveaway_id]
    save_giveaways()

    embed = discord.Embed(title="🚫 Giveaway Cancelled 🚫", color=0xff0000)
    embed.add_field(name="Prize", value=giveaway.prize, inline=False)
    embed.set_footer(text=f"Cancelled by {ctx.author.name}")

    await ctx.send(embed=embed)

@bot.hybrid_command(name="list", description="List all active giveaways")
async def list_giveaways(ctx):
    active = [g for g in active_giveaways.values() if not g.ended]
    if not active:
        await ctx.send("There are no active giveaways at the moment.")
        return

    embed = discord.Embed(title="Active Giveaways", color=0x00ff00)
    for giveaway in active:
        channel = bot.get_channel(giveaway.channel_id)
        embed.add_field(
            name=f"Giveaway in {channel.name}",
            value=f"Prize: {giveaway.prize}\nWinners: {giveaway.winners}\nEntries: {len(giveaway.participants)}\nEnds: <t:{int(giveaway.end_time)}:R>",
            inline=False
        )

    await ctx.send(embed=embed)

@bot.hybrid_command(name="giveaway_settings", description="Update giveaway embed settings")
@commands.has_permissions(manage_messages=True)
async def giveaway_settings_command(ctx):
    embed = create_settings_embed(ctx.guild)
    view = GiveawaySettingsView(ctx)
    await ctx.send(embed=embed, view=view)


@bot.hybrid_command(name="refresh", description="Manually refresh slash commands")
@commands.has_permissions(administrator=True)
async def refresh(ctx):
    await ctx.defer()
    await bot.tree.sync()
    await ctx.send("Slash commands have been refreshed!")

bot.remove_command('help')
@bot.hybrid_command(name="help", description="Show help information for the Giveaway Bot")
async def help_command(ctx):
    embed = discord.Embed(title="🎉 Giveaway Bot Help", 
                          description="Welcome to the Giveaway Bot! Here's how to use our fantastic features with slash commands:", 
                          color=0x00ff00)

    embed.add_field(name="📜 General Commands", value="""
```
/help     - Show this help message
/list     - List all active giveaways
```
""", inline=False)

    embed.add_field(name="🎁 Giveaway Commands", value="""
```
/giveaway - Start a new giveaway
/reroll   - Reroll winners for the last ended giveaway
/cancel   - Cancel the current giveaway in the channel
```
""", inline=False)

    embed.add_field(name="🛠️ Admin Commands", value="""
```
/refresh  - Manually refresh slash commands (Admin only)
/giveaway_settings - to customize your giveaway message !
```
""", inline=False)

    embed.add_field(name="📝 How to Start a Giveaway", value="""
1. Use `/giveaway` command
2. Fill in the required information:
   • Prize
   • Duration (e.g., 1h 30m, 2d)
   • Number of Winners
   • Additional Notes (optional)
3. Choose requirements (if any):
   • Role Requirement
   • Server Requirement
4. Confirm and launch!
""", inline=False)

    embed.add_field(name="💡 Tips", value="""
> • Use Discord's time format in chat: `<t:TIMESTAMP:R>`
> • Mention roles like this: `@RoleName`
> • Use emojis to make your giveaways more fun! 🎈🎊🥳
> • Slash commands work in both servers and DMs!
""", inline=False)

    embed.set_footer(text="Happy Giveaway Hosting! 🎉")

    await ctx.send(embed=embed)

async def end_giveaway(giveaway_id):
    giveaway = active_giveaways.get(giveaway_id)
    if not giveaway or giveaway.ended:
        return

    channel = bot.get_channel(giveaway.channel_id)
    if not channel:
        return

    giveaway.ended = True
    save_giveaways()

    try:
        message = await channel.fetch_message(giveaway.message_id)
        
        if not giveaway.participants:
            embed = discord.Embed(title="🎉 Giveaway Ended 🎉", color=0xff0000)
            embed.description = f"The giveaway for **{giveaway.prize}** has ended, but no one participated. 😢"
        else:
            winners = random.sample(list(giveaway.participants), min(giveaway.winners, len(giveaway.participants)))
            winner_mentions = [f"<@{winner}>" for winner in winners]

            embed = discord.Embed(title="🎉 Giveaway Ended! 🎉", color=0x00ff00)
            embed.add_field(name="Prize", value=giveaway.prize, inline=False)
            embed.add_field(name="Winners", value="\n".join(winner_mentions), inline=False)
            embed.description = f"Congratulations, {', '.join(winner_mentions)}! You've won the giveaway for **{giveaway.prize}**!"

        embed.set_footer(text=f"Hosted by {message.guild.get_member(giveaway.host_id).display_name}")

        # Disable the entry button
        view = GiveawayView(giveaway_id)
        for item in view.children:
            item.disabled = True

        await message.edit(embed=embed, view=view)

    except discord.errors.NotFound:
        print(f"Giveaway message {giveaway.message_id} not found. It may have been deleted.")
    except Exception as e:
        print(f"Error updating giveaway message: {e}")


@tasks.loop(seconds=3)  # Check more frequently
async def check_giveaways():
    current_time = datetime.datetime.now().timestamp()
    ended_giveaways = [gid for gid, g in active_giveaways.items() if current_time >= g.end_time and not g.ended]
    
    for giveaway_id in ended_giveaways:
        await end_giveaway(giveaway_id)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
    await bot.change_presence(activity=discord.Game(name="Hosting Giveaways!"))
    check_giveaways.start()
    
    # Refresh slash commands when the bot starts
    print("Refreshing slash commands...")
    await bot.tree.sync()
    print("Slash commands refreshed!")
    
if __name__ == "__main__":
    # Replace 'YOUR_BOT_TOKEN' with your actual bot token
    bot.run(DISCORD_TOKEN)

