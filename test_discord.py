import subprocess
from openai_adapter import OpenAIAdapter
from time import sleep
import signal
import os
from VoiceMaker import VoiceMaker
from play_sound import PlaySound

voice_maker = VoiceMaker()
play_sound = PlaySound()
ignore_message = ["ご視聴ありがとうございました", ""]

def run_asr():
    """Run the asr.py script and capture the output."""
    return subprocess.Popen(
        ['python', 'asr.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

def process_transcription(transcription: str, openai_adapter: OpenAIAdapter):
    """Send transcription to OpenAI and get the response."""
    if transcription in ignore_message:
        return
    message = openai_adapter.create_message("user", transcription)
    response = openai_adapter.chat_completions([message])
    return response

def main():
    openai_adapter = OpenAIAdapter()
    
    # Start the transcription process
    process = run_asr()

    def terminate_process(signum, frame):
        """Terminate the subprocess when test.py exits."""
        print("Terminating transcription process...")
        process.terminate()
        process.wait()  # Wait for the process to terminate gracefully

    # Handle termination signals (e.g., CTRL+C)
    signal.signal(signal.SIGINT, terminate_process)  # Handle interrupt signal (Ctrl+C)
    signal.signal(signal.SIGTERM, terminate_process)  # Handle terminate signal
    
    try:
        while True:
            # Capture transcription output from asr.py
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                transcription = output.strip()
                print(f"[Transcription]: {transcription}")
                
                # Send transcription to OpenAI and get the response
                response = process_transcription(transcription, openai_adapter)
                if response is not None:
                    response_voice = voice_maker.make_voice_style_bert_vits2(response)
                    play_sound.play_sound(response_voice)
                    print(f"[Response]: {response}")
            
            sleep(0.25)

    except KeyboardInterrupt:
        # Gracefully handle KeyboardInterrupt (Ctrl+C)
        print("\nExiting...")

    finally:
        # Ensure the subprocess is terminated
        terminate_process(None, None)

    print("\nTranscription process ended.")

if __name__ == "__main__":
    main()