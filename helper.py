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



active_giveaways = {}

# Load giveaway settings
def load_giveaway_settings():
    if os.path.exists("giveaway_settings.json"):
        with open("giveaway_settings.json", "r") as f:
            return json.load(f)
    return {}

# Save giveaway settings
def save_giveaway_settings(settings):
    with open("giveaway_settings.json", "w") as f:
        json.dump(settings, f)



def save_giveaways():
    data = {k: v.to_dict() for k, v in active_giveaways.items()}
    with open("giveaways.json", "w") as f:
        json.dump(data, f)

def load_giveaways():
    if os.path.exists("giveaways.json"):
        with open("giveaways.json", "r") as f:
            data = json.load(f)
        return {k: Giveaway.from_dict(v) for k, v in data.items()}
    return {}


async def get_role(interaction, role_input):
    try:
        # Check if the input is a role ID
        role = interaction.guild.get_role(int(role_input))
        if role:
            return role
    except ValueError:
        pass

    # If not an ID, search by name
    role = discord.utils.get(interaction.guild.roles, name=role_input)
    if role:
        return role

    # If role is not found, return None
    return None
