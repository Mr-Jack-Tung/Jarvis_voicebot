# Gemini Audio Chatbot
This is a voice-based chatbot powered by Google's Gemini AI model. It allows you to interact with the AI using your voice or text.

- Author: Mr. Jack Tung
- Create: 11 May 2024 - 11 PM

## Prerequisites

- Python 3.6 or higher
- A Google API key
- `mpg123` installed on your system
- https://github.com/Uberi/speech_recognition
- https://github.com/pndurette/gTTS
- https://github.com/mem0ai/mem0

## Setup

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up environment variables:**

    -   Create a `.env` file in the `gemini_audio_chatbot` directory.
    -   Add your OpenAI and Google API keys to the `.env` file:

        ```
        GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
        MEM0_API_KEY=YOUR_MEM0_API_KEY
        ```

## Usage

1.  **Run the chatbot:**

    ```bash
    python gemini_audio_chatbot/main.py
    ```

2.  **Interact with the chatbot:**

    -   To use voice input, press Enter (empty input) when prompted.
    -   To use text input, type your message and press Enter.
    -   Type `exit`, `quit`, `thoát`, or `thoat` to exit the program.

## Optional arguments

-   `--slow`: Run the chatbot in slow speech mode.

    ```bash
    python gemini_audio_chatbot/main.py --slow
    ```

## Troubleshooting

-   If you encounter issues with audio playback, make sure `mpg123` is installed correctly.
-   If you encounter issues with speech recognition, make sure your microphone is configured correctly.
-   If you encounter API errors, make sure your API keys are valid and have sufficient quota.

## License

This project is licensed under the MIT License.
