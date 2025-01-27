import os
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from dotenv import load_dotenv

class DiscordBot(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} がログインしました！")

    @commands.command()
    async def hello(self, ctx):
        await ctx.send("Hello!")

class DiscordAdapter:
    def __init__(self):
        # Load the token
        self.token = os.getenv("DISCORD_BOT_TOKEN")
        if not self.token:
            raise ValueError("Discordのトークンが見つかりませんでした")
        
        # Set up intents
        self.intents = discord.Intents.default()
        self.intents.messages = True
        self.intents.message_content = True
        self.bot = commands.Bot(command_prefix="!", intents=self.intents)

    def run(self):
        # Add the Cog before running the bot
        print("Adding Cog...")
        self.bot.add_cog(DiscordBot(self.bot))
        print("Running the bot...")
        self.bot.run(self.token)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()

    # Run the bot
    discord_adapter = DiscordAdapter()
    discord_adapter.run()
