![hedra-livekit](https://github.com/user-attachments/assets/8475de63-811a-4ff7-8631-e7733c868ef1)

# Hedra Avatar Examples

This directory contains various examples demonstrating how to integrate Hedra visual avatars with LiveKit voice agents. Hedra provides realistic avatar generation and animation capabilities that can be synchronized with AI voice agents.

## Overview

Each subdirectory contains a different implementation pattern or use case for Hedra avatars:

### 1. Education Avatar (`education_avatar/`)
**Purpose**: Interactive educational assistant specializing in Roman Empire history

<img width="1208" height="1177" alt="" src="https://github.com/user-attachments/assets/6f6fdd78-f28f-4df8-9b1a-68e035511968" />

**Key Features**:
- Flash card creation and management
- Interactive quizzes with multiple choice questions
- Socratic teaching method
- RPC communication for UI interactions
- Modern React frontend with dark theme

**Components**:
- `agent.py` - Educational agent with teaching capabilities
- `avatar.png` - Avatar image for the tutor
- `education-frontend/` - Modern Next.js frontend application
  - Flash card components with flip animations
  - Quiz components with progress tracking
  - Dark-themed UI matching modern design standards
  - Real-time RPC communication with the agent

**Use Case**: Educational applications, tutoring systems, or any scenario requiring interactive learning tools

## Common Patterns

### Avatar Session Management
All examples create a Hedra avatar session that connects to the voice agent session:
```python
avatar_session = hedra.AvatarSession(
    avatar_participant_identity="unique-id",
    avatar_image=avatar_image,
)
await avatar_session.start(session, room=ctx.room)
```

### Image Loading
Static avatar examples use a common pattern for loading avatar images:
```python
for ext in ['.png', '.jpg', '.jpeg']:
    image_path = os.path.join(avatar_dir, f'avatar{ext}')
    if os.path.exists(image_path):
        avatar_image = Image.open(image_path)
        break
```

## Frontend Integration

The education avatar includes a complete frontend example showing:
- How to handle RPC communication between frontend and agent
- Implementing interactive UI components (flash cards, quizzes)
- Managing state synchronization
- Dark theme styling for modern applications

### 2. Pipeline Avatar (`pipeline_avatar/`)
**Purpose**: Basic static avatar implementation using the standard voice pipeline

**Key Features**:
- Uses a pre-existing avatar image (avatar.png)
- Standard voice pipeline with STT → LLM → TTS flow
- Multi-language support with turn detection
- Noise cancellation enabled

**Components**:
- `agent.py` - Main agent implementation
- `avatar.png` - Static avatar image

**Use Case**: Simple avatar display with traditional voice assistant pipeline

### 3. Realtime Avatar (`realtime_avatar/`)
**Purpose**: Low-latency avatar using OpenAI's realtime API

**Key Features**:
- Uses OpenAI's realtime model for faster response times
- Minimal configuration for quick setup
- Static avatar image display
- Voice Activity Detection (VAD) with Silero

**Components**:
- `agent.py` - Realtime agent implementation
- `avatar.png` - Static avatar image

**Use Case**: When you need the fastest possible response times with visual presence

### 4. Dynamically Created Avatar (`dynamically_created_avatar/`)
**Purpose**: Generate avatars on-the-fly based on user descriptions

**Key Features**:
- Uses OpenAI to generate avatar images dynamically
- Function calling to trigger avatar creation/recreation
- Unique participant identities for each avatar
- Can remove and recreate avatars during conversation

**Components**:
- `agent.py` - Dynamic avatar generation logic

**Use Case**: Personalized avatars, role-playing scenarios, or when users want to customize their assistant's appearance

## Getting Started

1. **Choose an example** based on your use case:
   - Need fast responses? → Use `realtime_avatar`
   - Want a standard voice assistant? → Use `pipeline_avatar`
   - Need dynamic avatar generation? → Use `dynamically_created_avatar`
   - Building educational content? → Use `education_avatar`


2. **Add your avatar image** (for static examples):
   - Place a `avatar.png`, `avatar.jpg`, or `avatar.jpeg` in the example directory
   - Image should be appropriate for facial animation

3. **Configure your agent**:
   - Update the agent instructions
   - Choose appropriate STT/TTS providers
   - Configure any specific features (function calling, RPC methods, etc.)

4. **For frontend examples**:
   - Navigate to the frontend directory
   - Run `npm install` or `pnpm install`
   - Configure environment variables
   - Run `npm run dev` to start the development server

## Technical Notes

- All avatars use LiveKit's participant system for real-time communication
- Avatar sessions must be started before the agent session begins
- The avatar participant appears as a separate participant in the room
- Frontend communication uses LiveKit's RPC (Remote Procedure Call) system

## Environment Variables

Ensure you have the necessary environment variables set:
- `LIVEKIT_URL` - Your LiveKit server URL
- `LIVEKIT_API_KEY` - LiveKit API key
- `LIVEKIT_API_SECRET` - LiveKit API secret
- `HEDRA_API_KEY` For Avatar generation
- Your API keys for specific LLM/TTS/STT providers

## Best Practices

1. **Avatar Images**: Use high-quality portrait images with clear facial features
2. **State Management**: For complex interactions, use the userdata pattern (see education example)
3. **Frontend Integration**: Use RPC for bidirectional communication between agent and UI
