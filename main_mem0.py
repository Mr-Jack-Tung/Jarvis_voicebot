import google.generativeai as genai
# import pyaudio
import speech_recognition as sr
import gtts
import os
import sys
import threading
import signal
import time
from dotenv import load_dotenv
from mem0 import MemoryClient

# Load environment variables
load_dotenv(dotenv_path="gemini_audio_chatbot/.env")

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

os.environ["MEM0_API_KEY"] = os.getenv("MEM0_API_KEY")

# Initialize mem0 client
memory = MemoryClient()

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

def speak(text, lang="vi", slow=False):
    """
    Convert text to speech using Google Text-to-Speech and play it using mpg123.
    
    Args:
        text (str): The text to convert to speech
        lang (str): Language code (default: 'vi' for Vietnamese)
        slow (bool): Whether to speak slowly
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
        tts = gtts.gTTS(text=text, lang=lang, slow=slow)
        tts.save(output_file)
        print("▶️ Playing audio... (Press Ctrl+C to stop)")
        
        # Create a thread to monitor the interrupt flag with a timeout
        # def monitor_interrupt():
        #     global interrupt_flag
        #     max_time = 60  # Maximum time to play audio (60 seconds)
        #     elapsed = 0
            
        #     while not interrupt_flag and elapsed < max_time:
        #         time.sleep(0.1)
        #         elapsed += 0.1
        #         if interrupt_flag:
        #             os.system("pkill mpg123")
        #             break
            
        #     # If we reach max time, force stop
        #     if elapsed >= max_time and not interrupt_flag:
        #         print("⏱️ Maximum audio playback time reached, stopping...")
        #         interrupt_flag = True
        #         os.system("pkill mpg123")
        
        # Start the monitoring thread
        # monitor_thread = threading.Thread(target=monitor_interrupt)
        # monitor_thread.daemon = True
        # monitor_thread.start()
        
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

def set_identity(name, age, hometown):
    """
    Set the identity of the AI assistant in memory
    
    Args:
        name (str): Name of the AI
        age (str): Age of the AI
        hometown (str): Hometown of the AI
    """
    user_id = "default_user"
    memory.add([{"role": "system", "content": f"My name is {name}."}], user_id=user_id, output_format="v1.1")
    memory.add([{"role": "system", "content": f"I am {age} years old."}], user_id=user_id, output_format="v1.1")
    memory.add([{"role": "system", "content": f"I am from {hometown}."}], user_id=user_id, output_format="v1.1")

def think(user_input, user_id, memory):
    print("🤔 Gemini is thinking...")
    
    try:
        # Retrieve relevant memories from mem0
        relevant_memories = memory.search(query=user_input, user_id=user_id, limit=5, output_format="v1.1")
        # print("\nRetrieved memories:", relevant_memories)
        memories_str = "\n".join(f"- {entry['memory']}" for entry in relevant_memories['results'])
        print("\nRetrieved memories:\n", memories_str)

        # Interact with Gemini API
        system_prompt = f"""You are a helpful AI named Mai. You are 18 years old and from Cần Thơ. 
Because you are young, you should always refer to yourself as 'em' and the user as 'anh'. 
If the user's question is unclear, ask clarifying questions to understand their intent. 
If you are still unable to understand the question, provide a general response. 
Answer the question based on query and memories.
User Memories:
{memories_str}"""

        model = genai.GenerativeModel('models/gemini-2.5-flash-preview-04-17')
        response = model.generate_content(system_prompt + "\n" + user_input)
        gemini_response = response.text.strip().replace("**", "").replace("^^", "")
        return gemini_response
    except Exception as e:
        print(f"❌ Error interacting with Gemini API: {e}")
        return None
        
def main():
    """Main function to run the Gemini Audio Chatbot"""
    print("=== Gemini Audio Chatbot ===")
    print("- Press Enter (empty input) to use microphone")
    print("- Type your message to use text input")
    print("- Type 'exit', 'quit', or press Ctrl+C to exit the program")
    print("===============================")
    user_id = "default_user"
    
    # Uncomment to set identity at startup
    # set_identity("Mai", "18", "Cần Thơ")
    
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
            gemini_response = think(user_input, user_id, memory)    
            print("\n💬 Mai: {}".format(gemini_response))
            
            # Speak the response
            speak(gemini_response, lang="vi", slow=False)
            
            # Store the conversation in mem0
            memory.add([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": gemini_response}
            ], user_id=user_id, output_format="v1.1")
            
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            speak("Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn.", lang="vi")

if __name__ == "__main__":
    try:
        # Register signal handler for Ctrl+C
        signal.signal(signal.SIGINT, signal_handler)
        
        # Start the main application
        print("🚀 Starting Gemini Audio Chatbot...")
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
