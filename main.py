# Trigger point for the whole program
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Access the value of API_KEY
token = os.environ.get("token")

# intents allows bots to subscribe only to specific events they are interested in receiving.
class MyBot(commands.Bot):
    def __init__(self, prefix):
        intents = (
            discord.Intents.default()
        )  # this disables message_content so we have to enable it again
        intents.message_content = True
        super().__init__(command_prefix=prefix, intents=intents)

    async def setup_hook(self):
        await self.load_extension("challenge")
        await self.load_extension("view")
        await self.load_extension("tactics")
        await self.tree.sync(guild=None)

if __name__ == "__main__":
    client = MyBot()     #client = MyBot(prefix="!"), also ctx.user.id should become ctx.author.id
    client.run(token)