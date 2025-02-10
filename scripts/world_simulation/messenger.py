import discord
from discord.message import Message
from discord.guild import Guild
from discord.channel import VoiceChannel, DMChannel
from scripts.sound.voice_chat import VoiceChat
from scripts.adapters.openai_adapter import OpenAIAdapter
from scripts.memory.memory import ShortTermMemory
from scripts.commands.action_manager import ActionManager
from dotenv import load_dotenv
import os
import logging

class Contact:
    def __init__(self, name: str, channel: DMChannel):
        self.name = name
        self.channel = channel
        self.last_read_message_id = None

class Messenger:
    def __init__(self, 
                 voice_chat: VoiceChat,
                 adapter: OpenAIAdapter,
                 memory: ShortTermMemory,
                 action_manager: ActionManager):
        
        # 参照するクラス
        self.voice_chat = voice_chat
        self.adapter = adapter
        self.memory = memory
        self.action_manager = action_manager

        # 自分関連のコンタクト
        self.user = None
        self.contacts: dict[str, Contact] = {}
        self.guild: Guild = None
        self.voice_channel: VoiceChannel = None
        self.dev_dm_channel: DMChannel = None

        # トークン
        self.guild_id = int(os.getenv('GUILD_ID'))
        self.voice_channel_name = os.getenv('VOICE_CHANNEL_NAME')
        self.dev_dm_id = int(os.getenv('DEV_DM_ID'))

        # 未読メッセージの総数
        self.unread_messages_count = 0

    async def add_guild_members(self):
        # Add all guild members to own DM Contact (and also dev dm channel)
        for member in self.guild.members:
            if member == self.user:
                continue
            if member.dm_channel == None:
                await member.create_dm()
            if member.dm_channel.id == self.dev_dm_id:
                self.dev_dm_channel = member.dm_channel
            new_contact = Contact(name=member.global_name, channel=member.dm_channel)
            self.contacts[member.global_name] = new_contact
        logging.info("Added all guild members to own contact.")

    async def receive_dm(self, message: Message):
        self.unread_messages_count += 1
        author_name = message.author.global_name
        contact = self.contacts.get(author_name)
        if contact == None:
            # Add message author to own contact list
            self.contacts[author_name] = Contact(author_name, message.channel)
        else:
            # Check for last read message
            last_read_id = contact.last_read_message_id
            if last_read_id is None:
                self.contacts[author_name].last_read_message_id = message.id
                
            
        await self.memory.add(f"スマホに{self.unread_messages_count}件の通知が来ました：\n[{author_name}]からのメッセージです。[スマホを開く]ことでチェックできます。", narrate=False)
        # query = self.action_manager.ask(f"[{author_name}]からの返信が来ました。どうしますか？(10文字程度)")
        # await self.memory.add(query, role='assistant', narrate=False)
        return

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
            logging.info(f"Left the voice channel.")
        else:
            logging.warning(f"I'm not in voice channel!")

    # TODO Now only work for dev direct message
    async def read_dm_str(self, global_name="シン", limit=5):
        is_unread_start = False
        contact = self.contacts.get(global_name)  # Use .get() to avoid KeyError if not found
        if not contact:
            raise ValueError(f"No contact found for {global_name}")

        messages = f"[{global_name}との会話記録]"

        # Make sure the async for loop runs in a proper async context
        try:
            # Fetch messages in oldest-first order
            messages_list: list[Message] = []
            async for message in contact.channel.history(limit=None, oldest_first=True):  # Fetch all messages in oldest-first order
                messages_list.append(message)

            # Limit the messages to the most recent `limit` messages
            if limit is not None and len(messages_list) > limit:
                messages_list = messages_list[-limit:]  # Keep only the last `limit` messages

            # Process the messages
            for message in messages_list:
                if ((contact.last_read_message_id is None or message.id > contact.last_read_message_id)) and is_unread_start == False:
                    is_unread_start = True
                    messages += "(\n--------------ここからは未読のメッセージ--------------)"
                if is_unread_start:
                    self.unread_messages_count -= 1
                messages += f"\n[現実世界の時間{message.created_at}][{message.author.global_name}]{message.content}"
            if self.unread_messages_count <= 0:
                self.unread_messages_count = 0
            contact.last_read_message_id = messages_list[-1].id
        except Exception as e:
            logging.error(f"Error while fetching messages: {e}")

        return messages


    # TODO Now only work for dev direct message
    async def send_dm(self, message, name=None):
        if name is None:
            if self.dev_dm_channel is None:
                logging.error("dev_dm_channel is not set!")
                return
            await self.dev_dm_channel.send(message)