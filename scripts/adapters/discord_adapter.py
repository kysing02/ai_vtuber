# bot.py
import os
import subprocess
import tempfile
import wave
import discord
import asyncio
from discord.ext import commands
from discord.message import Message
from discord.guild import Guild
from discord.channel import VoiceChannel
from discord.member import Member
from discord import PCMVolumeTransformer, FFmpegPCMAudio
from dotenv import load_dotenv
from scripts.sound.voice_chat import VoiceChat
from scripts.adapters.vtube_studio_adapter import VTSAdapter
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.file_manager import FileManager, FilePath

class DiscordBot:
    def __init__(self, voice_chat: VoiceChat, vts: VTSAdapter, adapter: OpenAIAdapter):
        # Configures intents
        intents = discord.Intents.default()
        intents.messages = True # Enable message event
        intents.message_content = True # Required to read message content
        intents.members = True # Enable member events (e.g., on_member_join)
        intents.voice_states = True # Enable voice state events

        # Initialize the client
        self.client = discord.Client(intents=intents)
        self.voice_chat = voice_chat
        self.adapter = adapter
        
        # Load the bot token
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        self.guild_id = os.getenv('GUILD_ID')
        self.voice_channel_name = os.getenv('VOICE_CHANNEL_NAME')
        
        # Register events
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        self.client.event(self.on_member_join)

        # Airi specific parameters
        self.guild = None
        self.voice_channel = None

    async def on_ready(self):
        print(f'{self.client.user} has connected to Discord!')
        self.guild: Guild = discord.utils.get(self.client.guilds, id=int(self.guild_id))
        print(f'{self.client.user} is connected to the guild: {self.guild.name} (id: {self.guild.id})')
        self.voice_channel: VoiceChannel = discord.utils.get(self.guild.voice_channels, name=self.voice_channel_name)
        # Check guild members
        members = '\n - '.join([member.name for member in self.guild.members])
        print(f'Guild Members:\n - {members}')
        
        # Set the bot to appear offline
        await self.set_invisible()

    async def on_message(self, message: Message):
        # Ignore bot's own messages
        if message.author == self.client.user:
            return

        # Handle public messages
        if message.content == "!msg":
            response = "This is a test message."
            await message.channel.send(response)
        
        # System level commands-------------------------------------------------
        if message.content == "!voice_join":
            await self.join_voice_chat()

        elif message.content == "!voice_leave":
            await self.leave_voice_chat()
        
        elif message.content == "!force_end":
            raise KeyboardInterrupt
        
        elif message.content == "!invisible":
            await self.set_invisible()
        
        elif message.content == "!online":
            await self.set_online()

        else:
            profile = FileManager.read(FilePath.PROMPT_VOICE_CHAT)
            response = self.adapter.chat_completions([self.adapter.create_message('system', profile),
                                                    self.adapter.create_message('user', message.content)])
            await message.channel.send(response)
        # ----------------------------------------------------------------------
        
        # Handle other messages
        print("Received:", message)

    async def set_invisible(self):
        await self.client.change_presence(status=discord.Status.invisible)
        print(f"{self.client.user} is now invisible.")

    async def set_online(self):
        await self.client.change_presence(status=discord.Status.online)
        print(f'{self.client.user} is now online.')

    async def on_member_join(self, member: Member):
        await member.create_dm()
        await member.dm_channel.send(
            f'Hi {member.name}, welcome to my Discord server!'
        )

    # Functions to control bot--------------------------------------------------
    async def join_voice_chat(self):
        vc = await self.voice_channel.connect()
        print(f"Joined {self.voice_channel.name}")
        # Start the voice chat session
        await self.voice_chat.start()

    async def leave_voice_chat(self):
        if self.guild.voice_client:
            # Stop the VoiceChat session
            await self.voice_chat.end()

            # Disconnect the bot from the voice channel
            await self.guild.voice_client.disconnect()
            print(f"Left the voice channel.")
        else:
            print(f"I'm not in voice channel!")
    # --------------------------------------------------------------------------
    def run_bot(self):
        self.client.run(self.token)

if __name__ == "__main__":
    from scripts.sound.voice_chat import VoiceChat
    from scripts.sound.VoiceMaker import VoiceMaker
    from scripts.adapters.openai_adapter import OpenAIAdapter
    from scripts.sound.play_sound import PlaySound
    load_dotenv()
    vts = VTSAdapter()
    if asyncio.run(vts.connect_auth()):
        voice_chat = VoiceChat(
            adapter=OpenAIAdapter(),
            voice_maker=VoiceMaker(),
            play_sound=PlaySound(),
            vts=vts
        )
        bot = DiscordBot(voice_chat, vts, adapter=OpenAIAdapter())
        bot.run_bot()
