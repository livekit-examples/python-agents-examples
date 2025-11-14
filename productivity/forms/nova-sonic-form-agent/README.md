# Nova Sonic Form Agent

An AI-powered voice interview application that conducts job interviews and automatically fills out application forms through natural conversation.

## Overview

Nova Sonic Form Agent demonstrates the power of [LiveKit Agents](https://docs.livekit.io/agents) by creating an interactive job interview experience. The AI interviewer conducts a professional interview while simultaneously populating a job application form based on the candidate's spoken responses.

## Key Features

- **Voice-Driven Interview**: Engage in a natural conversation with an AI interviewer
- **Real-Time Form Population**: Watch as your responses automatically fill the application form
- **Smart Section Navigation**: The form highlights active sections as the interview progresses
- **Professional Interview Flow**: Covers experience, achievements, motivations, and career goals
- **Live Transcription**: See the conversation transcribed in real-time
- **RPC Integration**: Seamless communication between the AI agent and the frontend using LiveKit's RPC capabilities

## How It Works

1. **Start the Interview**: The AI interviewer greets you and begins the conversation
2. **Answer Questions**: Speak naturally about your experience, skills, and career goals
3. **Watch the Magic**: The form fields populate automatically as you speak
4. **Section Highlighting**: The form scrolls and highlights the section being discussed
5. **Submit**: Once all sections are complete, the application is submitted

## Form Sections

The application form includes:

### Professional Experience
- Current Role
- Company
- Years of Experience
- Key Achievements

### Interview Questions
- Why are you interested in this position?
- What are your greatest strengths?
- Challenging situation examples
- 5-year career goals
- Questions for the interviewer

## Technical Implementation

This frontend uses:
- **Next.js** for the application framework
- **LiveKit JavaScript SDK** for real-time communication
- **RPC handlers** for form updates from the AI agent
- **Motion/Framer** for smooth animations
- **Tailwind CSS** for styling

The AI agent communicates with the frontend through RPC calls to:
- Update individual form fields
- Update multiple fields at once
- Highlight active form sections
- Submit the completed application

## Getting Started

### Prerequisites

You'll need a Nova Sonic AI agent running to power the interview. The agent should be configured to conduct job interviews and make RPC calls to update the form.

### Installation

```bash
# Clone the repository
git clone
cd nova-sonic-form-agent

# Install dependencies
pnpm install

# Copy environment variables
cp .env.example .env.local

# Configure your LiveKit credentials in .env.local
```

### Running the Application

```bash
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Configuration

Edit `.env.local` to configure:
- `LIVEKIT_URL`: Your LiveKit server URL
- `LIVEKIT_API_KEY`: Your LiveKit API key
- `LIVEKIT_API_SECRET`: Your LiveKit API secret
