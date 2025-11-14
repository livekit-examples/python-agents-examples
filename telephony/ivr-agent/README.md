# IVR Navigator Agent

An intelligent voice agent that navigates Interactive Voice Response (IVR) systems using LiveKit's voice agents, allowing users accomplish custom tasks through external phone menu systems.

## Overview

**NavigatorAgent** - A voice-enabled agent that listens to IVR menu options, interprets the choices, and automatically sends DTMF (dual-tone multi-frequency) codes to navigate through phone systems based on a user-defined task.

## Features

- **Task-Based Navigation**: Define your goal, and the agent intelligently navigates IVR menus to accomplish it
- **DTMF Code Automation**: Automatically sends touch-tone codes to interact with phone systems
- **Real-time Visual Feedback**: See DTMF codes being pressed in the web interface
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Large Language Model (LLM) using OpenAI
  - Text-to-Speech (TTS) using Cartesia
  - Voice Activity Detection (VAD) using Silero
- **SIP Integration**: Connects to phone systems via SIP trunks
- **Web Frontend**: React-based interface for initiating calls and monitoring progress

## How It Works

1. User defines a task in the web interface (e.g., "Check my account balance")
2. User enters the phone number they want to call
3. The agent connects to the phone system via SIP
4. As the IVR presents menu options, the agent listens and interprets them
5. Based on the task, the agent automatically presses the appropriate DTMF codes
6. Visual feedback shows which codes are being pressed in real-time
7. The agent continues navigating until the task is completed or requires human intervention

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - OpenAI (for LLM capabilities)
  - Deepgram (for speech-to-text)
  - Cartesia (for text-to-speech)
- SIP trunk configured in LiveKit for phone connectivity
- Node.js and pnpm (for the frontend)

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
   LIVEKIT_HOST=your_livekit_host
   OPENAI_API_KEY=your_openai_key
   DEEPGRAM_API_KEY=your_deepgram_key
   CARTESIA_API_KEY=your_cartesia_key
   SIP_TRUNK_ID=your_sip_trunk_id
   ```

## Running the Agent

1. Start the agent:
   ```bash
   python agent.py dev
   ```

2. In a separate terminal, start the Flask backend:
   ```bash
   python app.py
   ```

3. In another terminal, navigate to the frontend directory and start the React app:
   ```bash
   cd ivr-agent-frontend
   pnpm install
   pnpm dev
   ```

The agent will be ready to accept calls through the web interface at `http://localhost:5173`.

## Architecture Details

### Main Classes

- **NavigatorAgent**: The core agent class that handles IVR navigation
- **UserData**: Stores session-specific data including the task and DTMF cooldown timing
- **send_dtmf_code**: Function tool that sends DTMF codes with a 3-second cooldown to prevent rapid firing

### Agent Session Flow

1. SIP participant connects to the LiveKit room
2. Task is extracted from participant attributes
3. Agent session is initialized with voice providers
4. Agent receives task-specific instructions
5. Agent listens to IVR and uses the LLM to decide which DTMF codes to send

### Frontend Integration

- React app provides task input and phone number entry
- Real-time visualization of agent state and DTMF codes being pressed
- WebSocket connection to LiveKit room for live updates

### Why Flask Backend?

While not strictly necessary (a Next.js app could handle both frontend and API calls), this example includes a Flask backend specifically to demonstrate how to use LiveKit's Python API library for making API calls. The Flask server handles:
- Generating LiveKit tokens for room access
- Making API calls to initiate SIP calls
- Serving as an example of Python-based LiveKit integration

In production, you could consolidate these functions into your frontend framework of choice.

## Customization

1. **Modify Agent Instructions**: Update the prompt template in the `on_enter` method to change how the agent interprets tasks
2. **Change Voice Providers**: Replace Deepgram, OpenAI, or Cartesia with other supported providers in the `entrypoint` function
3. **Adjust DTMF Timing**: Modify the cooldown period in the `send_dtmf_code` function (currently 3 seconds)
4. **Extend Task Capabilities**: Add more sophisticated task parsing or multi-step navigation logic
