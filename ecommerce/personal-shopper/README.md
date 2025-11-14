# Personal Shopper Agent

A multi-agent voice-enabled personal shopping assistant example that handles customer inquiries, sales, and returns using LiveKit's voice agents.

## Overview

This system employs three specialized agents that work together to provide comprehensive customer service:

1. **TriageAgent** - The initial point of contact that identifies customers and routes them to the appropriate department
2. **SalesAgent** - Assists customers with product selection and order placement
3. **ReturnsAgent** - Handles return requests and provides order history information

## Features

- **Multi-Agent Architecture**: Seamless transfer between specialized agents with context preservation
- **Customer Identification**: Persistent customer database tracks shoppers and their order history
- **Context Preservation**: Conversation history transfers between agents for continuity
- **Order Management**: Complete order workflow from item selection to checkout
- **Return Processing**: Access order history and process returns with reasons
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Large Language Model (LLM) using OpenAI GPT-4o-mini
  - Text-to-Speech (TTS) using Cartesia
  - Voice Activity Detection (VAD) using Silero
- **SQLite Database**: Persistent storage for customers and orders

## How It Works

1. Customer connects and is greeted by the Triage agent
2. Triage agent asks for the customer's name and identifies them in the system
3. Based on the customer's needs, they are transferred to either:
   - Sales agent for making purchases
   - Returns agent for processing returns
4. Agents can transfer customers between departments as needed
5. All customer information and order history persists across sessions
6. Context and conversation history follows the customer between agents

## Prerequisites

- Python 3.10+
- `livekit-agents`>=1.0
- LiveKit account and credentials
- API keys for:
  - OpenAI (for LLM capabilities)
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

```bash
python personal_shopper.py console
```

The agent will connect and start with the Triage agent ready to assist customers.

## Architecture Details

### Main Classes

- **UserData**: Stores session data including customer information, current order, and agent references
- **BaseAgent**: Parent class providing common functionality like context preservation and agent transfer
- **TriageAgent**: Routes customers to appropriate departments
- **SalesAgent**: Handles product selection and order placement
- **ReturnsAgent**: Processes returns and provides order history

### Agent Transfer Flow

1. Current agent's context is preserved in UserData
2. Transfer function creates personalized transition message
3. Next agent receives truncated conversation history
4. Customer identification persists across transfers

### Database Schema

The SQLite database (`customer_data.db`) contains:
- **customers**: Stores customer names and IDs
- **orders**: Stores order details as JSON with customer references

### Prompt Management

Agent personalities and instructions are loaded from YAML files in the `prompts/` directory:
- `triage_prompt.yaml`: Instructions for initial customer routing
- `sales_prompt.yaml`: Guidelines for sales interactions
- `returns_prompt.yaml`: Return processing instructions

## Customization

1. **Modify Agent Behavior**: Edit the YAML prompt files to change agent personalities and instructions
2. **Add New Agents**: Create new agent classes inheriting from BaseAgent and register them in the entrypoint
3. **Extend Order Management**: Add more fields to the order structure or implement inventory tracking
4. **Change Voice Providers**: Replace Deepgram, OpenAI, or Cartesia with other supported providers