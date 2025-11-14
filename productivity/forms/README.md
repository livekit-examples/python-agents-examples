# Nova Sonic Form Agent

A voice-driven AI interview system that demonstrates the power of LiveKit Agents by conducting professional job interviews and automatically populating application forms through natural conversation.

## Overview

Nova Sonic Form Agent is a full-stack application that showcases real-time voice AI capabilities:
- **AI Agent Backend**: Python-based LiveKit agent that conducts structured interviews
- **React Frontend**: Real-time form that updates as candidates speak
- **Voice Processing**: AWS Realtime for natural conversation and Silero VAD for voice detection
- **RPC Communication**: Seamless agent-to-frontend updates using LiveKit's RPC system

## Architecture

```
nova-sonic/
├── form_agent.py              # AI agent backend (Python)
└── nova-sonic-form-agent/     # React frontend (Next.js)
    ├── components/
    │   ├── form-session-view.tsx    # Main form interface
    │   └── session-view.tsx         # Standard chat interface
    └── README.md
```

## How It Works

1. **User Connection**: Candidate connects to the frontend application
2. **Agent Initialization**: Python agent starts and highlights the first form section
3. **Structured Interview**: Agent conducts interview in this order:
   - Professional Experience (role, company, years, achievements)
   - Interview Questions (5 standard questions)
   - Application submission
4. **Real-time Updates**: As candidate speaks, the agent:
   - Extracts information from responses
   - Sends RPC calls to update form fields
   - Highlights active sections
   - Provides visual feedback
5. **Form Submission**: Once complete, the application is submitted

## Key Features

### AI Agent (Backend)
- **Structured Interview Flow**: Follows a predefined interview sequence
- **Natural Language Processing**: Extracts relevant information from conversational responses
- **Smart Capitalization**: Automatically formats names, companies, and roles
- **Progress Tracking**: Monitors which sections have been completed

### Frontend Application
- **Live Form Updates**: Fields populate in real-time as you speak
- **Section Highlighting**: Visual indicators show which part is being discussed
- **Smooth Animations**: Framer Motion for polished transitions
- **Transcript Display**: See the conversation in real-time

## Technical Implementation

### RPC Communication
The agent communicates with the frontend via RPC calls:
```python
# Update single field
await send_form_update_to_frontend("updateField", {
    "field": "currentRole",
    "value": "Software Engineer"
})

# Update multiple fields
await send_form_update_to_frontend("updateMultipleFields", {
    "fields": {
        "currentRole": "Software Engineer",
        "company": "Tech Corp"
    }
})

# Highlight section
await send_form_update_to_frontend("highlightSection", {
    "section": "experience"
})
```

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- LiveKit Cloud account or self-hosted LiveKit server
- AWS credentials (for AWS Realtime model)

### Backend Setup

1. Install Python dependencies:
```bash
cd nova-sonic
pip install -r requirements.txt
```

2. Create `.env` file with your credentials:
```env
LIVEKIT_URL=your-livekit-url
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-west-2
```

3. Run the agent:
```bash
python form_agent.py
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd nova-sonic-form-agent
```

2. Install dependencies:
```bash
pnpm install
```

3. Configure environment:
```bash
cp .env.example .env.local
# Edit .env.local with your LiveKit credentials
```

4. Start the development server:
```bash
pnpm dev
```

5. Open [http://localhost:3000](http://localhost:3000)
