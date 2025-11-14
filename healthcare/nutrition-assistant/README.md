# Nutrition Assistant Agent

A voice-enabled nutrition tracking assistant that helps users log their food consumption and monitor daily nutritional intake using LiveKit's voice agents.

## Overview

**NutritionAssistant** - An AI-powered voice agent that listens to users describe their meals, automatically logs food consumption with nutritional information, and provides real-time tracking of daily calorie and macronutrient intake.

## Features

- **Voice-Based Food Logging**: Simply tell the agent what you've eaten, and it automatically records it
- **Nutritional Information Tracking**: Automatically estimates and tracks calories, protein, carbs, and fats
- **Real-time Dashboard**: Visual display of daily nutrition totals and food history
- **Persistent Storage**: SQLite database stores food consumption history
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using OpenAI Realtime
  - Large Language Model (LLM) using OpenAI GPT-4o Realtime
  - Text-to-Speech (TTS) using OpenAI Realtime voice (Sage)
  - Voice Activity Detection (VAD) using Silero
- **Noise Cancellation**: Integrated BVC noise cancellation for clearer voice input
- **RPC Communication**: Real-time updates between agent and frontend using LiveKit RPC

## How It Works

1. User clicks "Start a conversation" in the web interface
2. The agent greets the user and is ready to track food consumption
3. User describes what they've eaten (e.g., "I just had a chicken salad for lunch")
4. The agent uses AI to estimate nutritional information if not provided
5. Food consumption is logged to the SQLite database
6. The agent confirms what was recorded
7. Dashboard updates in real-time showing daily totals and food history
8. User can ask for daily summaries at any time

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - OpenAI (for Realtime model access)
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
   OPENAI_API_KEY=your_openai_key
   ```

## Running the Agent

1. Start the agent:
   ```bash
   python agent.py dev
   ```

2. In a separate terminal, navigate to the frontend directory and start the Next.js app:
   ```bash
   cd nutrition-assistant-frontend
   pnpm install
   pnpm dev
   ```

The application will be available at `http://localhost:3000`. Click "Start a conversation" to begin tracking your nutrition.

## Architecture Details

### Main Classes

- **NutritionAssistant**: The core agent class that handles food logging and nutrition tracking
- **NutritionUserData**: Stores user session data including participant identity
- **consumed_food**: Function tool that records food consumption with nutritional data
- **get_daily_calories**: Function tool that retrieves daily nutrition totals

### Database Schema

The SQLite database (`nutrition_tracker.db`) stores food consumption records with:
- Food name and timestamp
- Participant identity (currently using a fixed test user)
- Nutritional information (calories, protein, carbs, fats)
- Indexed by participant and date for efficient queries

### Agent Features

- **Automatic Nutritional Estimation**: If users don't provide specific nutritional values, the AI estimates them
- **Confirmation Messages**: Agent always confirms what was logged after recording
- **Daily Summaries**: Users can ask for their daily totals at any time
- **Encouraging Feedback**: Agent provides supportive messages about healthy eating

### Frontend Integration

- Next.js app with real-time nutrition dashboard
- Displays daily totals for calories and macronutrients
- Shows chronological list of foods consumed today
- Updates automatically via RPC when new foods are logged

## Customization

1. **Modify Agent Personality**: Update the instructions in the `NutritionAssistant` constructor to change the agent's behavior
2. **Change Voice Settings**: Replace the OpenAI Realtime voice or adjust voice parameters in the `entrypoint` function
3. **Extend Nutritional Tracking**: Add more nutritional fields (fiber, sugar, sodium, etc.) to the database schema and tools
4. **User Authentication**: Replace the fixed participant ID with actual user authentication for multi-user support