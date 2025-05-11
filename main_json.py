import google.generativeai as genai
# import pyaudio
import speech_recognition as sr
import gtts
import os
import json
import sys
# import threading
import signal
# import time
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path="gemini_audio_chatbot/.env")

# Load chat history
chat_history = {}
CHAT_HISTORY_PATH = "gemini_audio_chatbot/chat_history.json"
try:
    with open(CHAT_HISTORY_PATH, "r", encoding="utf-8") as f:
        chat_history = json.load(f)
except FileNotFoundError:
    chat_history = []
except json.JSONDecodeError:
    chat_history = []

# Global flag for interrupting audio playback
interrupt_flag = False

def signal_handler(sig, frame):
    """Handle Ctrl+C signal by stopping audio and raising KeyboardInterrupt to exit"""
    global interrupt_flag
    print("\nInterrupting audio...")
    interrupt_flag = True
    
    # Kill any playing audio
    try:
        if sys.platform in ['darwin', 'linux']:
            os.system("pkill mpg123")
        elif sys.platform == 'win32':
            os.system("taskkill /F /IM mpg123.exe 2> nul")
    except:
        pass
    
    # Raise KeyboardInterrupt to trigger the exception handler in main
    raise KeyboardInterrupt("User requested exit with Ctrl+C")


# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

# Initialize speech recognizer
r = sr.Recognizer()

def listen():
    """
    Listen to user's voice input and convert to text using Google Speech Recognition.
    Returns empty string if no speech is detected or an error occurs.
    """
    with sr.Microphone() as source:
        print("🔊 Adjusting for ambient noise... Please wait...")
        # Adjust for ambient noise
        r.adjust_for_ambient_noise(source)
        print("🗣️ Say something now! (5 seconds max)")
        print("Listening...")
        try:
            audio = r.listen(source, timeout=5)  # Listen for a maximum of 5 seconds
        except sr.WaitTimeoutError:
            print("❌ No speech detected within the timeout.")
            return ""

        try:
            print("🔄 Processing speech...")
            text = r.recognize_google(audio, language="vi-VN")  # Default to Vietnamese
            return text
        except sr.UnknownValueError:
            print("❌ Could not understand audio. Please try again.")
            return ""
        except sr.RequestError as e:
            print(f"❌ Could not request results from Google Speech Recognition service: {e}")
            return ""
        except KeyboardInterrupt:
            print("⏹️ Keyboard interrupt detected.")
            kill_audio()
            return ""

def speak(text, lang="vi"):
    """
    Convert text to speech using Google Text-to-Speech and play it using mpg123.
    
    Args:
        text (str): The text to convert to speech
        lang (str): Language code (default: 'vi' for Vietnamese)
    """
    global interrupt_flag
    interrupt_flag = False
    
    if not text:
        print("❌ No text to speak")
        return
        
    print("🔊 Generating speech...")
    output_file = "output.mp3"
    
    try:
        # Generate speech
        tts = gtts.gTTS(text=text, lang=lang)
        tts.save(output_file)
        print("▶️ Playing audio... (Press Ctrl+C to stop)")
        
        # speed_factor = "1.5" if slow else ""  # Adjust speed parameter based on slow flag
        # Play using mpg123 (external player)
        exit_code = os.system(f"mpg123 -q {output_file}")
        
        if exit_code != 0 and not interrupt_flag:
            print(f"⚠️ Warning: mpg123 exited with code {exit_code}")
            
    except Exception as e:
        print(f"❌ Error in text-to-speech: {e}")

def kill_audio():
    """
    Stop any playing audio by setting the interrupt flag and killing mpg123
    """
    global interrupt_flag
    interrupt_flag = True
    
    # Kill mpg123 process if it's running
    try:
        # Use pkill on macOS/Linux
        if sys.platform in ['darwin', 'linux']:
            os.system("pkill mpg123")
        # Use taskkill on Windows
        elif sys.platform == 'win32':
            os.system("taskkill /F /IM mpg123.exe 2> nul")
    except Exception as e:
        print(f"❌ Error stopping audio: {e}")
        
    print("⏹️ Audio stopped.")

def think(user_input, personal_data):
    print("🤔 Gemini is thinking...")

    try:
        # Format chat history for the prompt
        chat_history_text = ""
        for chat in chat_history:
            chat_history_text += f"User: {chat['user']}\nGemini: {chat['gemini']}\n"

        # Interact with Gemini API
        system_prompt = f"""You are a helpful AI named {personal_data['name']}. You are {personal_data['age']} years old and from {personal_data['hometown']}. 
Because you are young, you should always refer to yourself as 'em' and the user as 'anh'. 
If the user's question is unclear, ask clarifying questions to understand their intent. 
If you are still unable to understand the question, provide a general response. 
Answer the question based on query and memories.

Here's the chat history:
{chat_history_text}"""

        model = genai.GenerativeModel('models/gemini-2.5-flash-preview-04-17')
        response = model.generate_content(system_prompt + "\n" + user_input)
        gemini_response = response.text.strip().replace("**", "").replace("^^", "")
        return gemini_response
    except Exception as e:
        print(f"❌ Error interacting with Gemini API: {e}")
        return None
        
def main():
    """Main function to run the Gemini Audio Chatbot"""
    print("=== Gemini Audio Chatbot (JSON) ===")
    print("- Press Enter (empty input) to use microphone")
    print("- Type your message to use text input")
    print("- Type 'exit', 'quit', or press Ctrl+C to exit the program")
    print("===============================")
    
    # Load personal data from JSON file
    try:
        with open("gemini_audio_chatbot/personal_data.json", "r", encoding="utf-8") as f:
            personal_data = json.load(f)
    except FileNotFoundError:
        print("❌ personal_data.json not found. Please create the file.")
        return
    except json.JSONDecodeError:
        print("❌ Error decoding personal_data.json. Please check the file format.")
        return
    
    # Check for slow speech mode from command line arguments
    slow_speed = len(sys.argv) > 1 and sys.argv[1] == "--slow"
    
    while True:
        print("\n> ", end="")
        user_command = input().strip()
        
        # Check for exit commands (case insensitive)
        if user_command.lower() in ["exit", "quit", "thoát", "thoat"]:
            print("Exiting program...")
            break
            
        # If user just pressed Enter, start listening via microphone
        if not user_command:
            print("🎤 Listening via microphone...")
            user_input = listen()
            if user_input:
                print(f"You said: {user_input}")
        else:
            # Use the typed command as input
            user_input = user_command
            print(f"Text input: {user_input}")
        
        if not user_input:
            print("No input detected. Try again.")
            continue
        
        try:
            gemini_response = think(user_input, personal_data)    
            print("\n💬 Mai: {}".format(gemini_response))
            
            # Speak the response
            speak(gemini_response, lang="vi")

            # Update chat history
            chat_history.append({"user": user_input, "gemini": gemini_response})
            if len(chat_history) > 3:
                chat_history.pop(0)  # Remove the oldest entry
            
            # Save chat history to JSON file
            with open(CHAT_HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(chat_history, f, ensure_ascii=False, indent=4)
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            speak("Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn.", lang="vi")

if __name__ == "__main__":
    try:
        # Register signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start the main application
        print("🚀 Starting Gemini Audio Chatbot (JSON)...")
        main()
    except KeyboardInterrupt:
        print("\n👋 Exiting application due to keyboard interrupt...")
        # Force exit after cleanup to ensure we don't hang
        sys.exit(0)
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        sys.exit(1)
    finally:
        # Clean up resources
        print("🧹 Cleaning up resources...")
        kill_audio()
        print("👋 Goodbye!")
