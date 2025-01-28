import discord
from discord.ext import commands
# import asyncio
import pyaudio 
# from scripts.sound.VoiceMaker import VoiceMaker
# from scripts.sound.play_sound import PlaySound
from scripts.adapters.openai_adapter import OpenAIAdapter
import subprocess
# from time import sleep
from dotenv import load_dotenv
import os
import signal

import tempfile
import wave

# Load environment variables
load_dotenv(override=True)
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")  # Replace with your server ID
VOICE_CHANNEL_NAME = os.getenv("VOICE_CHANNEL_NAME")  # Replace with the voice channel name

# Initialize bot and related components
intents = discord.Intents.default()
intents.messages = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
voice_maker = VoiceMaker()
play_sound = PlaySound()
ignore_message = ["ご視聴ありがとうございました", ""]

@bot.event
async def on_ready():
    print(f"Bot logged in as {bot.user}")

    # Find the guild and voice channel
    guild = discord.utils.get(bot.guilds, id=int(GUILD_ID))
    if not guild:
        print("Guild not found!")
        return

    voice_channel = discord.utils.get(guild.voice_channels, name=VOICE_CHANNEL_NAME)
    if not voice_channel:
        print(f"Voice channel '{VOICE_CHANNEL_NAME}' not found!")
        return

    # Attempt to connect to the voice channel
    try:
        vc = await voice_channel.connect()
        print(f"Joined voice channel: {VOICE_CHANNEL_NAME}")
        await listen_and_respond(vc)
    except Exception as e:
        print(f"Error connecting to the voice channel: {e}")

async def listen_and_respond(vc):
    openai_adapter = OpenAIAdapter()

    def run_asr():
        """Run the asr.py script and capture the output."""
        return subprocess.Popen(
            ['python', 'asr.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

    def process_transcription(transcription: str):
        """Send transcription to OpenAI and get the response."""
        if transcription in ignore_message:
            return None
        message = openai_adapter.create_message("user", transcription)
        response = openai_adapter.chat_completions([message])
        return response

    process = run_asr()

    def terminate_process():
        """Terminate the transcription process."""
        if process and process.poll() is None:
            print("Terminating transcription process...")
            process.terminate()
            process.wait()

    # Handle termination signals
    signal.signal(signal.SIGINT, lambda signum, frame: terminate_process())
    signal.signal(signal.SIGTERM, lambda signum, frame: terminate_process())

    try:
        while True:
            # Read transcription from asr.py
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                transcription = output.strip()
                print(f"[Transcription]: {transcription}")

                # Process transcription and generate response
                response = process_transcription(transcription)
                if response:
                    response_voice = voice_maker.make_voice_style_bert_vits2(response)
                    await play_response(vc, response_voice)
            await asyncio.sleep(0.25)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        terminate_process()

async def play_response(vc, response_voice):
    # Extract data and sample rate
    audio_data = response_voice["data"]
    sample_rate = response_voice["sample_rate"]

    # Save audio to a temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        temp_wav_name = temp_wav.name
        with wave.open(temp_wav_name, "wb") as wav_file:
            # Set WAV file parameters
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # Sample width in bytes (16-bit audio)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

    try:
        # Play audio from the temporary file
        vc.play(discord.FFmpegPCMAudio(source=temp_wav_name))
        while vc.is_playing():
            await asyncio.sleep(0.5)
    finally:
        # Clean up the temporary file
        os.remove(temp_wav_name)

@bot.event
async def on_voice_state_update(member, before, after):
    """Automatically reconnect if disconnected."""
    if member == bot.user and before.channel is not None and after.channel is None:
        print("Bot disconnected. Reconnecting...")
        guild = discord.utils.get(bot.guilds, id=int(GUILD_ID))
        voice_channel = discord.utils.get(guild.voice_channels, name=VOICE_CHANNEL_NAME)
        if voice_channel:
            try:
                await voice_channel.connect()
            except Exception as e:
                print(f"Error reconnecting to the voice channel: {e}")

if __name__ == "__main__":
    bot.run(TOKEN)
