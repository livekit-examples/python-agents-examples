# Tavus Avatar Agent

A LiveKit-powered educational AI agent that uses the Tavus to create an interactive study partner focused on teaching about the Fall of the Roman Empire.

Demo: https://www.youtube.com/watch?v=iuX5PDP73bQ

## Features

- **Conversational Teaching**: Uses the Socratic method to guide students through learning
- **Flash Cards**: Creates and manages flash cards for important concepts
- **Interactive Quizzes**: Builds multiple-choice quizzes to test knowledge retention
- **Visual Avatar**: Powered by Tavus for procedural visual generation
- **Voice Interaction**: Natural voice conversation using Deepgram STT and ElevenLabs TTS

## Prerequisites

- Python 3.10+
- LiveKit account
- Tavus account with configured avatar (replica_id and persona_id)
- API keys for:
  - OpenAI
  - Deepgram
  - ElevenLabs
  - Tavus

## Installation

1. Clone this repository
2. Install dependencies from the root level of `python-agents-examples`
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the parent directory with your API keys

## Configuration

Set the following environment variables in your `.env` file:

```
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key
DEEPGRAM_API_KEY=your_deepgram_key
TAVUS_API_KEY=your_tavus_key
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
```

Customize the avatar by changing the `replica_id` and `persona_id` in the `entrypoint` function.

## Usage

Run the agent with:

```
python tavus.py dev
```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd voice-assistant-frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm run dev
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

### Flash Cards

The agent automatically creates flash cards for important concepts. Users can flip cards through the UI or by asking the agent.

### Quizzes

The agent creates interactive quizzes with multiple-choice questions. After completion:
- Users receive immediate feedback on their performance
- Flash cards are automatically created for incorrectly answered questions

## Extending

To modify the agent's topic focus:
1. Update the instructions in the `AvatarAgent` class
2. Adjust the quiz templates and flash card content to match your subject matter
