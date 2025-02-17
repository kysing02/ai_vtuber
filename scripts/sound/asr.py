#! python3.7

import argparse
import os
import numpy as np
import speech_recognition as sr
from faster_whisper import WhisperModel
from datetime import datetime, timedelta
from queue import Queue
from time import sleep
from sys import platform
# Whisperモデルで動かす
from openai import OpenAI
import tempfile
import soundfile as sf
import json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="faster-whisper-large-v3-turbo-ct2", help="Model to use",
                        choices=["faster-whisper-large-v3-turbo-ct2"])
    parser.add_argument("--language", default="ja", help="Language for transcription (e.g., 'ja' for Japanese).")
    parser.add_argument("--energy_threshold", default=1000,
                        help="Energy level for mic to detect.", type=int)
    parser.add_argument("--record_timeout", default=3,
                        help="How real time the recording is in seconds.", type=float)
    parser.add_argument("--phrase_timeout", default=5,
                        help="Timeout between recordings.", type=float)
    parser.add_argument("--use_api", type=bool,
                        help="Use OpenAI Whisper API to process ASR")
    args = parser.parse_args()
    # Time to wait for a new response to come
    wait_time = 0.3
    # The last time a recording was retrieved from the queue.
    phrase_time = None
    # Thread safe Queue for passing data from the threaded recording callback.
    data_queue = Queue()
    # We use SpeechRecognizer to record our audio because it has a nice feature where it can detect when speech ends.
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    # Definitely do this, dynamic energy compensation lowers the energy threshold dramatically to a point where the SpeechRecognizer never stops recording.
    recorder.dynamic_energy_threshold = False
    # Ignore empty string or weird output
    ignore_messages = ["ご視聴ありがとうございました", "", "ご視聴ありがとうございました。", "おやすみなさい", "ご視聴ありがとうございました!"]

    # Important for linux users.
    # Prevents permanent application hang and crash by using the wrong Microphone
    if 'linux' in platform:
        mic_name = 'pulse'
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            if mic_name in name:
                source = sr.Microphone(sample_rate=16000, device_index=index)
                break
    else:
        source = sr.Microphone(sample_rate=16000)
        # Modification to use CABLE Input as microphone
        # mic_name = "CABLE Output"
        # for index, name in enumerate(sr.Microphone.list_microphone_names()):
        #     if mic_name in name:
        #         source = sr.Microphone(sample_rate=16000, device_index=index)
        #         break

    if (args.use_api):
        client = OpenAI()
    else:
        # Load / Download model
        model_path = args.model
        model = WhisperModel(model_path)

    record_timeout = args.record_timeout
    phrase_timeout = args.phrase_timeout

    transcription = ['']

    # Use the microphone source in the correct context
    if source:
        with source:
            recorder.adjust_for_ambient_noise(source)
    else:
        print("Microphone source not found.")
        return

    def record_callback(_, audio:sr.AudioData) -> None:
        """
        Threaded callback function to receive audio data when recordings finish.
        audio: An AudioData containing the recorded bytes.
        """
        # Grab the raw bytes and push it into the thread safe queue.
        data = audio.get_raw_data()
        data_queue.put(data)

    # Create a background thread that will pass us raw audio bytes.
    # We could do this manually but SpeechRecognizer provides a nice helper.
    recorder.listen_in_background(source, record_callback, phrase_time_limit=args.record_timeout)

    # Model loaded. Send ready signal
    print("ready")
    while True:
        try:
            now = datetime.utcnow()
            # Pull raw recorded audio from the queue.
            if not data_queue.empty():
                phrase_complete = False
                # If enough time has passed between recordings, consider the phrase complete.
                # Clear the current working audio buffer to start over with the new data.
                if phrase_time and now - phrase_time > timedelta(seconds=args.phrase_timeout):
                    phrase_complete = True
                # This is the last time we received new audio data from the queue.
                phrase_time = now
                
                # Combine audio data from queue
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()
                
                # Convert in-ram buffer to something the model can use directly without needing a temp file.
                # Convert data from 16 bit wide integers to floating point with a width of 32 bits.
                # Clamp the audio stream frequency to a PCM wavelength compatible default of 32768hz max.
                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

                # Read the transcription.
                if (args.use_api):
                    text = transcribe_with_openai(client, audio_np)
                else:
                    segments, _ = model.transcribe(audio_np, language=args.language)
                    text = "".join([segment.text for segment in segments]).strip()
                text = text.encode('cp932', errors='replace').decode('cp932')

                # If we detected a pause between recordings, add a new item to our transcription.
                # Otherwise edit the existing one.
                # if phrase_complete:
                if text not in ignore_messages:
                    transcription.append(text)
                # else:
                #     if len(transcription) > 1:
                #         transcription[-1] = text
                #     else:
                #         transcription.append(text)

            else:
                # Output the final transcription to stdout so it can be captured by the subprocess.
                if len(transcription) >= 1:
                    sleep(wait_time)
                    os.system('cls' if os.name=='nt' else 'clear')
                    print("\n".join(transcription), flush=True)
                    transcription.clear()
                    # Flush stdout.
                    print('', end='', flush=True)
                # Infinite loops are bad for processors, must sleep.
                sleep(0.1)
                
        except KeyboardInterrupt:
            break

def transcribe_with_openai(client, audio_np, language="ja"):
    temp_dir = tempfile.gettempdir()  # Get temp directory path
    temp_audio_path = os.path.join(temp_dir, "temp_audio.wav")

    # Save the audio as a WAV file
    sf.write(temp_audio_path, audio_np, samplerate=16000)

    with open(temp_audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-1",
            language=language,
        )

    # Clean up the temporary file
    os.remove(temp_audio_path)
    return response.text
    
    return response
if __name__ == "__main__":
    main()
