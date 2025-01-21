from transformers import pipeline
# Load the TTS pipeline with the fishaudio model
tts = pipeline("text-to-speech", model="fishaudio/fish-speech-1.5")

# Generate speech from text
text = "こんにちは！Fish Speechのテストです"
output = tts(text)

# Save the audio output to a file
with open("test.wav", "wb") as f:
    f.write(output["audio"])