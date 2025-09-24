# Note Taking Assistant with Medical Notes Frontend

This demo shows a medical note-taking assistant that transcribes conversations between doctors and patients, generating structured medical notes in real-time.

## Features

- Real-time transcription of conversations
- Automatic medical note generation using Cerebras LLM
- Live frontend display showing:
  - Current medical notes being generated
  - Recent transcriptions (last 5 sentences)
- RPC communication between backend agent and frontend

## Architecture

- **Backend Agent**: Python agent that handles transcription and note generation
- **Frontend**: Next.js application displaying notes and transcriptions in real-time
- **Communication**: Uses LiveKit RPC for real-time updates from backend to frontend

## Running the Application

### Prerequisites
- Python 3.10+
- Node.js 18+
- LiveKit credentials

### Backend Agent

1. Navigate to the project root:
```bash
cd demo-monolith
```

2. Install Python dependencies if not already installed:
```bash
pip install -r requirements.txt
```

3. Run the agent:
```bash
python complex-agents/note-taking-assistant/agent.py dev
```

### Frontend

1. Navigate to the frontend directory:
```bash
cd complex-agents/note-taking-assistant/note-taker-frontend
```

2. Install dependencies:
```bash
pnpm install
```

3. Run the development server:
```bash
pnpm dev
```

4. Open your browser to http://localhost:3000

## Usage

1. Start both the backend agent and frontend
2. Connect to the room from the frontend interface
3. Start speaking - the agent will transcribe your speech
4. Medical notes will be automatically generated and displayed on the left side
5. Recent transcriptions will appear in the top box
6. The full medical notes will accumulate in the main notes section

## How It Works

1. **Speech Capture**: User speech is captured and transcribed using Deepgram STT
2. **Buffering**: Transcriptions are buffered until 5 sentences are accumulated
3. **Note Generation**: Every 5 sentences are sent to Cerebras LLM for medical note generation
4. **RPC Updates**: The backend sends updates to the frontend via RPC with:
   - Current medical notes
   - Recent transcription (last 5 sentences processed)
5. **Frontend Display**: The frontend displays both the notes and recent transcriptions in real-time

## Medical Note Categories Tracked

- Chief complaints
- History of present illness
- Past medical history
- Allergies
- Medications
- Family history
- Social history