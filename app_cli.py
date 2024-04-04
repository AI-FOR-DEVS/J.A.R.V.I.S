import pyaudio
import wave
import tempfile
import math
import struct
import simpleaudio as sa
from speech2text import speech2text
from text2speech import text2speech
from groq_service import execute
from gmail_service import fetch_mails

# Audio parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
THRESHOLD = 1000  # Silence threshold
SILENCE_DURATION = 1  # Seconds of silence to signify end of command


def is_silent(data_chunk):
    """Check if the given audio chunk is silent."""
    rms = math.sqrt(sum(
        sample ** 2 for sample in struct.unpack("<" + "h" * (len(data_chunk) // 2), data_chunk)
    ) / len(data_chunk))
    return rms < THRESHOLD


def record_until_pause():
    """Record audio from the microphone until a pause is detected."""
    print("Listening... Speak now.")
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    frames = []
    silent_chunks = 0
    silent_chunks_threshold = int(SILENCE_DURATION * RATE / CHUNK)
    started = False

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        is_silence = is_silent(data)

        if not started:
            if not is_silence:
                started = True
                frames.append(data)
        else:
            frames.append(data)
            if is_silence:
                silent_chunks += 1
            else:
                silent_chunks = 0

            if silent_chunks > silent_chunks_threshold:
                break

    stream.stop_stream()
    stream.close()
    audio.terminate()

    if not frames:
        print("No speech detected.")
        return None

    temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    with wave.open(temp_audio.name, 'wb') as wave_file:
        wave_file.setnchannels(CHANNELS)
        wave_file.setsampwidth(audio.get_sample_size(FORMAT))
        wave_file.setframerate(RATE)
        wave_file.writeframes(b''.join(frames))

    return temp_audio.name


def play_audio_file(file_path):
    """Play the audio file."""
    try:
        wave_obj = sa.WaveObject.from_wave_file(file_path)
        play_obj = wave_obj.play()
        play_obj.wait_done()
    except Exception as e:
        print(f"Error playing audio file: {e}")


def process_audio(audio_path):
    """Process the audio file."""
    text = speech2text(audio_path)
    print(f"Recognized Text: {text}")

    generated_answer = execute(f"Please answer to the question: {text}")

    if "fetch_emails" in generated_answer:
        print("Call fetch mails")
        emails = fetch_mails()
        prompt = f"""
            Answer the users question: '{text}'. Don't call the fetch_mails.
            All Emails in Inbox:
            ---
            {emails}
            ---
        """

        generated_answer = execute(prompt)
        

    print(f"Generated Answer: {generated_answer}")
    # This function needs to return the path of the generated audio file
    generated_speech_path = text2speech(generated_answer)
    return generated_speech_path


def main():
    """Main function to orchestrate the listening, processing, and responding loop."""
    while True:
        audio_path = record_until_pause()
        if audio_path:
            response_audio_path = process_audio(audio_path)
            play_audio_file(response_audio_path)
        else:
            print("Listening again...")


if __name__ == "__main__":
    main()
