import os
import discord

class DiscordBot(discord.Client):
    def __init__(self, token):
        super().__init__()
    
    async def on_ready(self):
        print(f"{self.user}が準備できた")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    discord_adapter = DiscordBot(os.getenv("DISCORD_BOT_TOKEN"))
    discord_adapter.run()