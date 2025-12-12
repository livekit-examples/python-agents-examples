<p align="center">
  <img src="livekit-logo-dark.png" alt="LiveKit" height="80">
</p>

<h1 align="center">Python Agents Examples</h1>

<p align="center">
  <strong>A comprehensive collection of 77+ runnable examples for building voice, video, and telephony agents with LiveKit</strong>
</p>

<p align="center">
  <a href="https://docs.livekit.io/agents/"><img src="https://img.shields.io/badge/docs-livekit.io-blue" alt="Documentation"></a>
  <a href="https://github.com/livekit/agents"><img src="https://img.shields.io/badge/livekit--agents-1.0+-green" alt="LiveKit Agents"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.10+-yellow" alt="Python 3.10+"></a>
</p>

---

## Overview

This repository contains everything you need to learn and build production-ready voice AI agents using [LiveKit Agents](https://docs.livekit.io/agents/). From single-file quickstarts to multi-agent orchestration systems with companion frontends, these examples demonstrate real-world patterns and best practices.

```
python-agents-examples/
├── docs/examples/          # 50+ focused, single-concept demos
└── complex-agents/         # 20+ production-style applications with frontends
```

Every example includes **YAML frontmatter metadata** (title, category, tags, difficulty, description) for easy discovery by both humans and tooling.

---

## Quick Start

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.10+ | Required |
| pip / uv | Latest | Package management |
| LiveKit Account | — | [Sign up free](https://cloud.livekit.io) |
| Node.js | 18+ | Only for frontend demos |
| pnpm | Latest | Only for frontend demos |

### Installation

```bash
# Clone the repository
git clone https://github.com/livekit-examples/python-agents-examples.git
cd python-agents-examples

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the repository root:

```env
# Required - LiveKit credentials
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Provider keys (add as needed for specific examples)
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
CARTESIA_API_KEY=...
ELEVENLABS_API_KEY=...
ANTHROPIC_API_KEY=...
```

### Run Your First Agent

```bash
# Start an interactive voice session
python docs/examples/listen_and_respond/listen_and_respond.py console
```

The `console` argument opens an interactive terminal session where you can speak or type with the agent.

---

## Examples by Category

### Fundamentals

Start here to understand core agent concepts.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Listen and Respond](docs/examples/listen_and_respond/) | The simplest voice agent—listens and responds | Beginner |
| [Tool Calling](docs/examples/tool_calling/) | Add function tools agents can invoke | Beginner |
| [Context Variables](docs/examples/context_variables/) | Inject user context into agent instructions | Beginner |
| [Playing Audio](docs/examples/playing_audio/) | Play audio files within an agent | Beginner |
| [Repeater](docs/examples/repeater/) | Echo back exactly what the user says | Beginner |
| [Uninterruptable](docs/examples/uninterruptable/) | Complete responses without interruptions | Beginner |
| [Exit Message](docs/examples/exit_message/) | Handle graceful session endings | Beginner |

### Multi-Agent Systems

Build complex workflows with multiple specialized agents.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Agent Transfer](docs/examples/agent_transfer/) | Switch between agents mid-call using function tools | Intermediate |
| [Medical Office Triage](complex-agents/medical_office_triage/) | Multi-department routing with context preservation | Advanced |
| [Personal Shopper](complex-agents/personal_shopper/) | E-commerce with triage, sales, and returns agents | Advanced |
| [Doheny Surf Desk](complex-agents/doheny-surf-desk/) | Phone booking system with background observer agent | Advanced |

### Telephony & SIP

Voice AI for phone systems.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Answer Call](docs/examples/answer_call/) | Basic inbound call handling | Beginner |
| [Make Call](docs/examples/make_call/) | Outbound calling via SIP trunks | Beginner |
| [Warm Handoff](docs/examples/warm_handoff/) | Transfer calls to human agents | Intermediate |
| [SIP Lifecycle](docs/examples/sip_lifecycle/) | Complete call lifecycle management | Advanced |
| [Survey Caller](docs/examples/survey_caller/) | Automated surveys with CSV data collection | Intermediate |
| [IVR Navigator](complex-agents/ivr-agent/) | Navigate phone menus using DTMF | Advanced |

### Pipeline Customization

Intercept and modify the STT → LLM → TTS pipeline.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Simple Content Filter](docs/examples/simple_content_filter/) | Keyword-based output filtering | Beginner |
| [LLM Content Filter](docs/examples/llm_powered_content_filter/) | Dual-LLM moderation system | Advanced |
| [TTS Node Override](docs/examples/tts_node_modifications/) | Custom text replacements before speech | Intermediate |
| [Transcription Node](docs/examples/transcription_node/) | Modify transcriptions before LLM | Intermediate |
| [Short Replies Only](docs/examples/short_replies_only/) | Interrupt verbose responses | Beginner |
| [LLM Output Replacement](docs/examples/replacing_llm_output/) | Strip thinking tags from reasoning models | Intermediate |

### Vision & Multimodal

Agents that can see.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Gemini Live Vision](docs/examples/gemini_live_vision/) | Real-time vision with Gemini 2.0 | Beginner |
| [Vision Agent](complex-agents/vision/) | Camera vision with Grok-2 Vision | Intermediate |
| [Moondream Vision](docs/examples/moondream_vision/) | Add vision to non-vision LLMs | Intermediate |

### Avatars & Visual Agents

Bring your agent to life with animated avatars.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Hedra Pipeline Avatar](complex-agents/avatars/hedra/pipeline_avatar/) | Static image avatar with pipeline architecture | Intermediate |
| [Hedra Realtime Avatar](complex-agents/avatars/hedra/realtime_avatar/) | OpenAI Realtime + Hedra avatar | Intermediate |
| [Dynamic Avatar](complex-agents/avatars/hedra/dynamically_created_avatar/) | Create avatars on-the-fly | Intermediate |
| [Education Avatar](complex-agents/avatars/hedra/education_avatar/) | Teaching avatar with flash cards via RPC | Advanced |
| [Tavus Avatar](complex-agents/avatars/tavus/) | Tavus-powered avatar assistant | Intermediate |

### Translation & Multilingual

Break language barriers.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Pipeline Translator](docs/examples/pipeline_translator/) | English → French voice translation | Intermediate |
| [TTS Translator](docs/examples/tts_translator/) | Advanced translation with Gladia code-switching | Advanced |
| [Change Language](docs/examples/changing_language/) | Dynamic language switching via function tools | Intermediate |

### Metrics & Observability

Monitor and debug your agents.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [LLM Metrics](docs/examples/metrics_llm/) | Token counts, TTFT, throughput | Beginner |
| [STT Metrics](docs/examples/metrics_stt/) | Transcription timing and errors | Beginner |
| [TTS Metrics](docs/examples/metrics_tts/) | Speech synthesis performance | Beginner |
| [VAD Metrics](docs/examples/metrics_vad/) | Voice activity detection stats | Beginner |
| [Langfuse Tracing](docs/examples/langfuse_tracing/) | Full session tracing with Langfuse | Intermediate |

### Events & State

React to conversation events and manage state.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [Basic Events](docs/examples/basic_event/) | Register event listeners with on/off/once | Beginner |
| [Event Emitters](docs/examples/event_emitters/) | Custom event handling patterns | Beginner |
| [Conversation Monitoring](docs/examples/label_messages/) | Log and inspect conversation events | Beginner |
| [State Tracking](docs/examples/state_tracking/) | Complex NPC state with rapport system | Advanced |
| [RPC State Management](docs/examples/rpc_agent/) | CRUD operations over RPC | Advanced |

### Advanced Integrations

Connect to external services.

| Example | Description | Difficulty |
|---------|-------------|------------|
| [MCP Client (stdio)](docs/examples/stdio_mcp_client/) | Connect to local MCP servers | Beginner |
| [MCP Client (HTTP)](docs/examples/http_mcp_client/) | Connect to remote MCP servers | Beginner |
| [Home Automation](docs/examples/home_assistant/) | Control smart home devices | Intermediate |
| [RAG Voice Agent](docs/examples/rag/) | Vector search with Annoy + embeddings | Advanced |
| [Shopify Voice](complex-agents/shopify-voice-shopper/) | Voice shopping with MCP + Shopify | Advanced |

---

## Full Applications

These full-stack applications include both backend agents and React frontends.

### 🎮 Dungeons & Agents
> Voice-driven D&D RPG with narrator/combat agents, character progression, and turn-based combat.

```bash
cd complex-agents/role-playing
python agent.py dev

# In another terminal
cd role_playing_frontend && pnpm install && pnpm dev
```

**Features:** Multi-agent switching, dice mechanics, NPC generation, inventory system, combat AI

---

### 📞 Doheny Surf Desk
> Phone booking system with background observer agent and task groups.

```bash
cd complex-agents/doheny-surf-desk
python agent.py dev
```

**Features:** 5 specialized agents, LLM-based guardrails, sequential tasks, context injection

---

### 🔬 EXA Deep Researcher
> Voice-controlled research agent using EXA for web intelligence.

```bash
cd complex-agents/exa-deep-researcher
python agent.py dev

# In another terminal  
cd frontend && pnpm install && pnpm dev
```

**Features:** Background research jobs, RPC streaming, cited reports

---

### 🏥 Medical Office Triage
> Multi-department medical system with agent transfers.

```bash
cd complex-agents/medical_office_triage
python triage.py dev
```

**Features:** Triage → Specialist routing, chat history preservation, YAML prompts

---

### 🍔 Drive-Thru
> Fast food ordering system with menu management.

```bash
cd complex-agents/drive-thru/drive-thru-agent
python agent.py dev

# In another terminal
cd ../frontend && pnpm install && pnpm dev
```

---

### 📝 Nova Sonic Form Agent
> Job application interview with AWS Realtime.

```bash
cd complex-agents/nova-sonic
python form_agent.py dev

# In another terminal
cd nova-sonic-form-agent && pnpm install && pnpm dev
```

**Features:** AWS Realtime model, structured data collection, live form updates

---

## Provider Support

Examples demonstrate integration with these providers:

| Category | Providers |
|----------|-----------|
| **LLM** | OpenAI, Anthropic, Google Gemini, Groq, Cerebras, AWS Bedrock, X.AI |
| **STT** | Deepgram, AssemblyAI, Gladia, Cartesia |
| **TTS** | Cartesia, ElevenLabs, Rime, PlayAI, Inworld, OpenAI |
| **VAD** | Silero |
| **Avatar** | Hedra, Tavus |
| **Vision** | OpenAI GPT-4V, Google Gemini, X.AI Grok, Moondream |
| **Realtime** | OpenAI Realtime, Google Gemini Live, AWS Nova Sonic |

---

## Discovery Tools

### Browse the Index

The complete catalog lives in [`docs/index.yaml`](docs/index.yaml) with metadata for every example:

```yaml
- file_path: docs/examples/tool_calling/tool_calling.py
  title: Tool Calling
  category: basics
  tags: [tool-calling, deepgram, openai, cartesia]
  difficulty: beginner
  description: Shows how to use tool calling in an agent.
  demonstrates:
    - Using the most basic form of tool calling
```

### Find Examples by Tag

```bash
# Find all telephony examples
rg "tags:.*telephony" docs/index.yaml

# Find all advanced examples  
rg "difficulty: advanced" docs/index.yaml
```

### Frontmatter Search

Every Python example starts with YAML frontmatter:

```bash
# Find examples using specific providers
rg "tags:.*elevenlabs" -g "*.py"
```

---

## Testing

The repository includes testing utilities in `complex-agents/testing/`:

```python
# Basic greeting test
async def test_agent_greeting():
    session = await create_test_session()
    response = await session.generate_reply()
    assert "hello" in response.lower()
```

Run tests with pytest:

```bash
cd complex-agents/testing
pytest -v
```

---

## Resources

| Resource | Link |
|----------|------|
| LiveKit Agents Documentation | [docs.livekit.io/agents](https://docs.livekit.io/agents/) |
| LiveKit Agents GitHub | [github.com/livekit/agents](https://github.com/livekit/agents) |
| LiveKit Cloud | [cloud.livekit.io](https://cloud.livekit.io) |

---

## Contributing

We welcome contributions! Please open an issue or PR if you:

- Find a bug or have a suggestion
- Want to add a new example
- Improve documentation

---

<p align="center">
  <sub>Built with ❤️ by the <a href="https://livekit.io">LiveKit</a> team</sub>
</p>
