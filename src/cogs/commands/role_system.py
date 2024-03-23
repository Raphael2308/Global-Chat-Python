import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import os
import json
##########################################################################
load_dotenv()
config_location = os.getenv('config_location')
config_location = os.getenv('config_file')
with open(config_location, 'r') as file:
    config = json.load(file)
admin_guild = config["admin_guild"]
##########################################################################


class global_setup_commands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    @app_commands.command(name="test", description="Test Command")
    async def add_global(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Test", ephemeral=True)

async def setup(client:commands.Bot) -> None:
    await client.add_cog(global_setup_commands(client))