# Teleprompter Agent

A voice-synchronized teleprompter that automatically scrolls pre-written text to match the user's speech pace using LiveKit's voice agents.

## Overview

**TeleprompterAgent** - A voice-enabled agent that transcribes user speech in real-time and synchronizes teleprompter text scrolling to match what the user is saying, ensuring they always see what to say next.

## Features

- **Voice-Synchronized Scrolling**: Teleprompter text automatically moves to match the user's speech pace
- **Real-time Speech Tracking**: Transcribes user speech to determine current position in the script
- **Smart Text Matching**: Aligns transcribed speech with pre-written teleprompter content
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Cartesia
  - Voice Activity Detection (VAD) using default LiveKit settings
- **Frontend Text Editor**: Type or paste your script directly in the web interface
- **Teleprompter Mode**: Switch between editing and teleprompter modes

## How It Works

1. User types or pastes their script into the frontend text editor
2. User connects to the LiveKit room and enters "teleprompter mode"
3. As the user reads the script aloud, the agent transcribes their speech
4. The agent sends transcripts to the frontend via RPC
5. The frontend matches the transcript to the script text and scrolls accordingly
6. The teleprompter automatically advances to show upcoming text as the user speaks
7. User always sees what they need to say next, synchronized with their speech

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - Cartesia (for speech-to-text)
- Node.js and npm/pnpm (for the frontend)

## Installation

1. Clone the repository

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the parent directory with your API credentials:
   ```
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   CARTESIA_API_KEY=your_cartesia_key
   ```

## Running the Agent

1. Start the agent:
   ```bash
   python cartesia-ink.py dev
   ```

2. In a separate terminal, navigate to the frontend directory and start the Next.js app:
   ```bash
   cd teleprompter-frontend
   npm install
   npm run dev
   ```

The teleprompter will be available at `http://localhost:3000`.

## Architecture Details

### Main Components

- **Agent Session**: Manages the voice session and transcript events
- **Transcript Handler**: Listens for finalized transcripts and sends them via RPC
- **RPC Methods**:
  - `get_transcript_status`: Called by frontend to check connection status
  - `receive_transcript`: Called by agent to send transcript data to frontend

### Synchronization Flow

1. User pre-writes their script in the frontend editor
2. When teleprompter mode is activated, user begins reading
3. Cartesia STT processes the audio stream in real-time
4. When a transcript segment is finalized, the `user_input_transcribed` event fires
5. The agent sends the transcript to the frontend using RPC
6. Frontend matches the transcript against the pre-written script
7. Teleprompter scrolls to keep the current reading position centered
8. Upcoming text remains visible for the user to read next

### Frontend Integration

- Next.js application with text editor and teleprompter display
- Connects to LiveKit room for voice synchronization
- Registers RPC handler to receive real-time transcripts
- Implements text matching algorithm to sync scroll position
- Smooth scrolling animation for natural reading experience

## Customization

1. **Change STT Provider**: Replace Cartesia with another supported STT provider like Deepgram or OpenAI
3. **Text Matching Algorithm**: Enhance the matching logic to handle variations in speech (pauses, corrections, etc.)
4. **Frontend Display**: Customize the teleprompter appearance (font size, colors, scroll smoothness, preview lines)