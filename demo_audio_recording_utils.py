# poetry run python3 --version
# Python 3.10.17
# By downgrading to NumPy 1.26.4, we provided a version that PyTorch 2.2.2 can properly interact with
# poetry run pip install numpy==1.26.4

# poetry add sounddevice scipy pydub

import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import pydub

def record_and_save_audio(filename="output.wav", duration=5, sample_rate=14400):
    """
    Records audio from the microphone and saves it to a WAV file.

    Args:
        filename (str): The name of the output WAV file.
        duration (int): The recording duration in seconds.
        sample_rate (int): The sample rate of the recording. 14400 | 44100
    """
    print(f"Recording for {duration} seconds...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.int16)
    sd.wait()  # Wait until recording is finished
    write(filename, sample_rate, audio_data)
    print(f"Recording saved to {filename}")


def convert_wav_to_mp3(wav_filename, mp3_filename):
    """
    Converts a WAV file to an MP3 file.

    Args:
        wav_filename (str): The path to the input WAV file.
        mp3_filename (str): The path to the output MP3 file.
    """
    try:
        audio = pydub.AudioSegment.from_wav(wav_filename)
        audio.export(mp3_filename, format="mp3")
        print(f"Converted {wav_filename} to {mp3_filename}")
    except Exception as e:
        print(f"Error converting {wav_filename} to MP3: {e}")


def record_and_save_mp3(filename="output.mp3", duration=5, sample_rate=14400):
    """
    Records audio from the microphone and saves it to an MP3 file.

    Args:
        filename (str): The name of the output MP3 file.
        duration (int): The recording duration in seconds.
        sample_rate (int): The sample rate of the recording. 14400 | 44100
    """
    print(f"Recording for {duration} seconds...")
    audio_data = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.int16)
    sd.wait()  # Wait until recording is finished

    audio_segment = pydub.AudioSegment(
        audio_data.tobytes(),
        frame_rate=sample_rate,
        sample_width=audio_data.dtype.itemsize,
        channels=1
    )
    audio_segment.export(filename, format="mp3")
    print(f"Recording saved to {filename}")


if __name__ == "__main__":
    # Example usage: record 10 seconds of audio and save to "my_recording.wav"
    record_and_save_audio("my_recording.wav", duration=3)
    # Example usage: record 10 seconds of audio and save to "my_recording.mp3"
    # record_and_save_mp3("my_recording.mp3", duration=10)
