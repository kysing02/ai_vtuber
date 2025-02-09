# bot.py
import os
import subprocess
import tempfile
import wave
import discord
import asyncio
import threading
import logging
from discord.ext import commands
from discord.message import Message
from discord.member import Member
from discord import PCMVolumeTransformer, FFmpegPCMAudio
from dotenv import load_dotenv
from scripts.sound.voice_chat import VoiceChat
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.memory.memory import ShortTermMemory
from scripts.commands.action_manager import ActionManager
from scripts.world_simulation.messenger import Messenger

class DiscordBot:
    def __init__(self, voice_chat: VoiceChat, adapter: OpenAIAdapter, short_term_memory: ShortTermMemory, action_manager: ActionManager):
        # Configures intents
        intents = discord.Intents.default()
        intents.messages = True # Enable message event
        intents.message_content = True # Required to read message content
        intents.members = True # Enable member events (e.g., on_member_join)
        intents.voice_states = True # Enable voice state events

        # Initialize the client
        self.client = discord.Client(intents=intents)

        # To pass to the messenger
        self.voice_chat = voice_chat
        self.adapter = adapter
        self.short_term_memory = short_term_memory
        self.action_manager = action_manager

        # Load the bot token
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        
        # Register events
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        
        self.task_future = None

    async def on_ready(self):
        self.task_future = asyncio.Future()
        # Initialize messenger class
        self.messenger = Messenger(self.voice_chat, self.adapter, self.short_term_memory, self.action_manager)

        logging.info(f'{self.client.user} has connected to Discord!')
        self.messenger.user = self.client.user
        self.messenger.guild = discord.utils.get(self.client.guilds, id=int(self.messenger.guild_id))
        logging.info(f'{self.client.user} is connected to the guild: {self.messenger.guild.name} (id: {self.messenger.guild_id})')
        self.messenger.voice_channel = discord.utils.get(self.messenger.guild.voice_channels, name=self.messenger.voice_channel_name)
        
        await self.messenger.add_guild_members()

    async def on_message(self, message: Message):
        # Ignore bot's own messages
        if message.author == self.client.user:
            return

        # System level commands (only allow for dev user)

        if message.author.dm_channel.id == self.messenger.dev_dm_id:
            if message.content == "!voice_join":
                await self.messenger.join_voice_chat()

            elif message.content == "!voice_leave":
                await self.messenger.leave_voice_chat()
            
            elif message.content == "!force_end":
                await self.client.close()
                raise KeyboardInterrupt
            
            elif message.content == "!invisible":
                await self.set_invisible()
            
            elif message.content == "!online":
                await self.set_online()

            elif message.content == "!msg":
                await message.channel.send("This is a test message.")
                await self.messenger.send_dm("Hello", None)
        
        # Check if this is private DM channel (Now Airi-chan only receive DM Messages - for sake of simplicity)
        if message.channel.id == message.author.dm_channel.id:
            await self.messenger.receive_dm(message)
        else:
            pass
             
        # Handle other messages
        print("Received:", message)

    async def send_dm(self, message, name=None):
        if name is None:
            if self.messenger.dev_dm_channel is None:
                logging.error("dev_dm_channel is not set!")
                return
            await self.messenger.dev_dm_channel.send(message)
        if self.task_future:  # If future exists, mark it as done
            self.task_future.set_result("Task completed successfully!")

    async def set_invisible(self):
        await self.client.change_presence(status=discord.Status.invisible)
        logging.info(f"{self.client.user} is now invisible.")

    async def set_online(self):
        await self.client.change_presence(status=discord.Status.online)
        logging.info(f'{self.client.user} is now online.')

    # async def on_member_join(self, member: Member):
    #     await member.create_dm()
    #     await member.dm_channel.send(f'Hi {member.name}, welcome to my Discord server!')

    def run_bot(self):
        self.client.run(self.token)

    def run_bot_in_thread(self):
        bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        bot_thread.start()

    def schedule_task(self, coro):
        """Safely schedule a coroutine in the bot's event loop."""
        return asyncio.run_coroutine_threadsafe(coro, self.client.loop)

if __name__ == "__main__":
    from scripts.sound.voice_chat import VoiceChat
    from scripts.sound.VoiceMaker import VoiceMaker
    from scripts.adapters.openai_adapter import OpenAIAdapter
    from scripts.sound.play_sound import PlaySound
    load_dotenv()
    vts = VTSAdapter()
    adapter = OpenAIAdapter()
    if asyncio.run(vts.connect_auth()):
        voice_chat = VoiceChat(
            adapter=adapter,
            voice_maker=VoiceMaker(),
            play_sound=PlaySound(),
            vts=vts
        )
        bot = DiscordBot(voice_chat, adapter, None, None)
        bot.run_bot_in_thread()
        import time
        time.sleep(5)
        bot.schedule_task(bot.send_dm("こんにちはー"))