# poetry run python3 --version
# Python 3.10.17
# By downgrading to NumPy 1.26.4, we provided a version that PyTorch 2.2.2 can properly interact with
# poetry run pip install numpy==1.26.4

# Install dependencies
# pip install soundfile sounddevice scipy torchaudio transformers

# Vietnamese end-to-end speech recognition using wav2vec 2.0
# https://huggingface.co/nguyenvulebinh/wav2vec2-base-vietnamese-250h

import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
import torch
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import os
import sys
import threading
import time
import soundfile as sf

# load model and tokenizer
# Using a smaller sampling rate as in demo_audio_transcript.py
processor = Wav2Vec2Processor.from_pretrained("nguyenvulebinh/wav2vec2-base-vietnamese-250h", sampling_rate=14400)
model = Wav2Vec2ForCTC.from_pretrained("nguyenvulebinh/wav2vec2-base-vietnamese-250h")
model.gradient_checkpointing_enable()

def transcribe_audio(audio_file_path):
    """
    Transcribes the audio file using the loaded Wav2Vec2 model.
    """
    try:
        # define function to read in sound file
        def map_to_array(batch):
            speech, _ = sf.read(batch["file"])
            batch["speech"] = speech
            return batch

        # load dummy dataset and read soundfiles
        ds = map_to_array({
            "file": audio_file_path
        })

        # tokenize
        input_values = processor(ds["speech"], return_tensors="pt", padding="longest").input_values  # Batch size 1

        # retrieve logits
        logits = model(input_values).logits

        # take argmax and decode
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids)
        return transcription[0] # Return the first transcription in the batch
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def record_audio_until_silence(filename="temp_recording.wav", sample_rate=14400, silence_threshold=500, silence_duration=2, max_duration=10):
    """
    Records audio from the microphone and stops after a period of silence or max duration.

    Args:
        filename (str): The name of the output WAV file.
        sample_rate (int): The sample rate of the recording.
        silence_threshold (int): The amplitude threshold below which audio is considered silent.
        silence_duration (int): The duration of silence in seconds to stop recording.
        max_duration (int): The maximum recording duration in seconds.
    """
    print("Press Enter to start recording...")
    input() # Wait for Enter key press

    print("Recording... Press Ctrl+C to stop manually.")

    audio_data = []
    silent_frames = 0
    frames_per_second = sample_rate
    start_time = time.time()

    # Flag to signal the timer thread to stop
    stop_timer_flag = False

    def timer_display():
        nonlocal stop_timer_flag
        while not stop_timer_flag:
            elapsed_time = time.time() - start_time
            remaining_time = max(0, max_duration - elapsed_time)
            # Use carriage return to overwrite the line
            print(f"Time remaining: {remaining_time:.1f} seconds", end='\r')
            time.sleep(0.1)
        print(" " * 30, end='\r') # Clear the timer line

    # Start the timer display thread
    timer_thread = threading.Thread(target=timer_display)
    timer_thread.daemon = True
    timer_thread.start()


    def callback(indata, frames, time, status):
        nonlocal audio_data, silent_frames
        if status:
            print(status, file=sys.stderr)
        audio_data.append(indata.copy())

        # Simple silence detection: check if the maximum amplitude in the frame is below the threshold
        if np.abs(indata).max() < silence_threshold:
            silent_frames += frames
        else:
            silent_frames = 0 # Reset silent frames if sound is detected

    try:
        with sd.InputStream(samplerate=sample_rate, channels=1, dtype=np.int16, callback=callback):
            while True:
                elapsed_time = time.time() - start_time
                # Check for silence duration or max duration
                if silent_frames >= silence_duration * frames_per_second or elapsed_time >= max_duration:
                    if elapsed_time >= max_duration:
                        print("\nMaximum recording duration reached.")
                    print("Stopping recording.")
                    break
                time.sleep(0.05) # Small delay to avoid busy waiting

    except KeyboardInterrupt:
        print("\nRecording stopped manually with Ctrl+C.")
    except Exception as e:
        print(f"\nAn error occurred during recording: {e}")
    finally:
        # Stop the timer thread
        stop_timer_flag = True
        timer_thread.join(timeout=0.5) # Join with a timeout


    if audio_data:
        # Concatenate recorded data
        recorded_audio = np.concatenate(audio_data, axis=0)
        write(filename, sample_rate, recorded_audio)
        print(f"Recording saved to {filename}")
        return filename
    else:
        print("No audio recorded.")
        return None

if __name__ == "__main__":
    temp_audio_file = "temp_recording.wav"
    while True:
        recorded_file = record_audio_until_silence(temp_audio_file)

        if recorded_file and os.path.exists(recorded_file):
            print("Transcribing...")
            transcription = transcribe_audio(recorded_file)
            if transcription:
                # Use ANSI escape codes for green color
                print("Transcription: \033[92m" + transcription + "\033[0m")

            # Clean up the temporary file
            os.remove(recorded_file)
            print(f"Removed temporary file: {recorded_file}")
        else:
            print("Could not transcribe.")

        # Ask user to continue
        print("\nPress Enter to record again, or any other key to exit.")
        if input() != "":
            break

    print("Exiting.")

'''
% python3 demo_auto_vietnamese_voice_transcript.py
Press Enter to start recording...

Recording... Press Ctrl+C to stop manually.
Stopping recording. secondss
Recording saved to temp_recording.wav
Transcribing...
Transcription: xin chào rất vui được làm quen với bạn
Removed temporary file: temp_recording.wav

Press Enter to record again, or any other key to exit.
'''