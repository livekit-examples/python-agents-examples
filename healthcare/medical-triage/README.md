# Medical Office Triage Agent

This project implements an intelligent medical office triage system using LiveKit's voice agents. The system features three specialized agents that work together to handle patient inquiries and route them to the appropriate department.

## Overview

The Medical Office Triage Agent system consists of three specialized agents:

1. **Triage Agent** - The initial point of contact that determines patient needs and routes them to the appropriate department
2. **Support Agent** - Handles medical services including appointment scheduling, prescription refills, medical records requests, and general healthcare questions
3. **Billing Agent** - Manages insurance information, copayments, medical bills, payment processing, and billing inquiries

## Features

- **Multi-Agent Architecture**: Three specialized agents that can seamlessly transfer calls between each other based on patient needs
- **Context Preservation**: When transferring between agents, the conversation history is preserved to avoid patients having to repeat information
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Large Language Model (LLM) using OpenAI GPT-4o-mini
  - Text-to-Speech (TTS) using Cartesia
  - Voice Activity Detection (VAD) using Silero

## How It Works

1. All calls start with the **Triage Agent**, which greets the patient and determines their needs
2. Based on the patient's request, the Triage Agent transfers them to either:
   - **Support Agent** for medical services (appointments, prescriptions, medical records)
   - **Billing Agent** for financial matters (insurance, bills, payment plans)
3. Agents can transfer patients between departments if needed, maintaining the full conversation context
4. Each agent has specific guidelines for handling their department's inquiries professionally and empathetically

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - OpenAI (for GPT-4o-mini)
  - Deepgram (for speech-to-text)
  - Cartesia (for text-to-speech)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API credentials:
   ```
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   OPENAI_API_KEY=your_openai_key
   DEEPGRAM_API_KEY=your_deepgram_key
   CARTESIA_API_KEY=your_cartesia_key
   ```

## Running the Agent

To run the medical office triage agent in console mode:

```bash
python triage.py console
```

This will start the agent system and allow you to interact with it through your console. The conversation will begin with the Triage Agent, who will assess your needs and transfer you to the appropriate department.

## Architecture Details

### BaseAgent Class
- Handles common functionality for all agents
- Manages context preservation during transfers
- Implements chat context truncation to maintain relevant conversation history
- Updates room attributes to track which agent is currently active

### Agent Transfer Flow
- Each agent has `transfer_to_*` methods decorated with `@function_tool`
- Transfers announce the handoff to the patient before switching agents
- Previous agent's context is preserved and passed to the new agent
- Chat history is truncated to keep the last 6 relevant messages

### Prompt Management
- Agent instructions are stored in YAML files in the `prompts/` directory
- Each agent has specific guidelines for their department
- Prompts emphasize professionalism, empathy, and HIPAA compliance

## Customization

You can customize the agents by:
1. Modifying the prompt files in `prompts/` directory
2. Adjusting the LLM model or other components in each agent's `__init__` method
3. Adding new transfer functions or tools to handle additional scenarios
4. Implementing additional agents for other departments