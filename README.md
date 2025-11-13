<div align="center">

# LiveKit Agents Examples

<p><strong>53 production-ready examples showcasing the power of LiveKit Agents</strong></p>

[![LiveKit Agents](https://img.shields.io/badge/LiveKit-Agents-00ADD8?style=flat-square)](https://docs.livekit.io/agents/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)](https://www.python.org/)
[![Examples](https://img.shields.io/badge/Examples-53-green?style=flat-square)](#examples)

<p>
  <a href="#getting-started">Getting Started</a> •
  <a href="#examples">Browse Examples</a> •
  <a href="https://docs.livekit.io/agents/">Documentation</a> •
  <a href="https://livekit.io/community">Community</a>
</p>

</div>

---

## Getting Started

### Prerequisites

- **Python 3.10+** with pip or uv
- **LiveKit account** ([Sign up free](https://cloud.livekit.io))
- **API keys** for AI providers (OpenAI, Deepgram, ElevenLabs, etc.)
- **Node.js 18+** and pnpm (for demos with web frontends)

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/livekit-examples/python-agents-examples.git
cd python-agents-examples

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the repository root:

```bash
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Add provider-specific keys as needed
OPENAI_API_KEY=your_openai_key
DEEPGRAM_API_KEY=your_deepgram_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

### Run Your First Example

```bash
# Try a simple voice agent
python hardware/pi-zero-transcriber/pi_zero_transcriber.py console

# Or explore a complex multi-agent system
python complex-agents/medical_office_triage/triage.py dev
```

---

## Examples

<details open>
<summary><h3>Avatars (5 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [Dynamically Created Avatar](avatars/hedra/dynamically_created_avatar/agent.py)
<kbd>intermediate</kbd>

Shows how to create an avatar dynamically in an agent.

**Key concepts:** `avatar` `openai` `deepgram`

</td>
<td width="50%">

#### [Education Avatar](avatars/hedra/education_avatar/agent.py)
<kbd>advanced</kbd>

Shows how to create an avatar that can help a user learn about the Fall of the Roman Empire using flash cards and quizzes.

**Key concepts:** `avatar` `openai` `deepgram` `hedra`

</td>
</tr>
<tr>
<td width="50%">

#### [Hedra Avatar with Pipeline](avatars/hedra/pipeline_avatar/agent.py)
<kbd>intermediate</kbd>

Visual avatar using Hedra with static image, pipeline architecture, and Inworld TTS

**Key concepts:** `hedra` `avatar` `static_image` `pipeline` `inworld_tts`

</td>
<td width="50%">

#### [Hedra Avatar with Realtime](avatars/hedra/realtime_avatar/agent.py)
<kbd>intermediate</kbd>

Visual avatar using Hedra with OpenAI Realtime model integration

**Key concepts:** `hedra` `avatar` `static_image` `openai_realtime`

</td>
</tr>
<tr>
<td width="50%">

#### [Tavus Avatar](avatars/tavus/tavus.py)
<kbd>intermediate</kbd>

Shows how to create a tavus avatar that can help a user learn about the Fall of the Roman Empire using flash cards and quizzes.

**Key concepts:** `avatar` `openai` `deepgram` `tavus`

</td>
<td width="50%">
</td>
</tr>
</table>

</details>

<details open>
<summary><h3>Complex Agents (18 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [Base Game Agent](complex-agents/role-playing/agents/base_agent.py)
<kbd>advanced</kbd>

Base class for RPG game agents with context preservation and state management

**Key concepts:** `rpg` `game-state` `agent-switching` `context-preservation` `rpc-communication`

</td>
<td width="50%">

#### [Combat Agent](complex-agents/role-playing/agents/combat_agent.py)
<kbd>advanced</kbd>

Specialized agent for handling turn-based combat encounters in RPG games

**Key concepts:** `rpg` `combat-system` `turn-based-combat` `npc-ai` `function-tools`

</td>
</tr>
<tr>
<td width="50%">

#### [D&D Role-Playing Game](complex-agents/role-playing/agent.py)
<kbd>advanced</kbd>

Dungeons & Dragons role-playing game with narrator and combat agents

**Key concepts:** `rpg` `game_state` `rpc_methods` `item_generation` `combat_system`

</td>
<td width="50%">

#### [EXA Deep Researcher](complex-agents/exa-deep-researcher/agent.py)
<kbd>advanced</kbd>

Voice-controlled deep research agent using EXA for web intelligence

**Key concepts:** `exa` `research` `voice_controlled` `background_jobs` `rpc_streaming`

</td>
</tr>
<tr>
<td width="50%">

#### [Game State Management](complex-agents/role-playing/core/game_state.py)
<kbd>intermediate</kbd>

Centralized game state management for RPG sessions with type-safe data structures

**Key concepts:** `rpg` `state-management` `dataclass` `session-data` `type-safety`

</td>
<td width="50%">

#### [IVR Phone System Navigator](complex-agents/ivr-agent/agent.py)
<kbd>advanced</kbd>

Agent that navigates phone IVR systems using DTMF codes

**Key concepts:** `ivr` `dtmf` `telephony` `sip` `participant_attributes`

</td>
<td width="50%">

#### [Item Generator](complex-agents/role-playing/generators/item_generator.py)
<kbd>advanced</kbd>

AI-powered procedural item generation system for RPG games

**Key concepts:** `rpg` `procedural-generation` `llm-generation` `yaml-configuration` `item-creation`

</td>
</tr>
<tr>
<td width="50%">

#### [Job Application Form Agent](complex-agents/nova-sonic/form_agent.py)
<kbd>advanced</kbd>

Interactive interview agent for job applications with AWS Realtime

**Key concepts:** `aws_realtime` `form_filling` `rpc_frontend` `interview` `structured_data`

</td>
<td width="50%">

#### [Medical Office Triage System](complex-agents/medical_office_triage/triage.py)
<kbd>advanced</kbd>

Multi-agent medical triage system with specialized departments

**Key concepts:** `multi_agent` `agent_transfer` `medical` `context_preservation` `chat_history`

</td>
</tr>
<tr>
<td width="50%">

#### [NPC Generator](complex-agents/role-playing/generators/npc_generator.py)
<kbd>advanced</kbd>

AI-powered NPC generation system with personality, backstory, and dynamic dialogue

**Key concepts:** `rpg` `procedural-generation` `character-creation` `personality-generation` `dialogue-system`

</td>
<td width="50%">

#### [Narrator Agent](complex-agents/role-playing/agents/narrator_agent.py)
<kbd>advanced</kbd>

Main storytelling agent for RPG games with voice acting and world interaction

**Key concepts:** `rpg` `storytelling` `npc-interaction` `voice-acting` `exploration`

</td>
</tr>
<tr>
<td width="50%">

#### [Note Taking Assistant](complex-agents/note-taking-assistant/agent.py)
<kbd>intermediate</kbd>

Shows how to use the Note Taking Assistant.

**Key concepts:** `complex-agents` `cerebras` `deepgram`

</td>
<td width="50%">

#### [Nutrition Tracker Assistant](complex-agents/nutrition-assistant/agent.py)
<kbd>advanced</kbd>

Nutrition tracking assistant with SQLite database and real-time updates

**Key concepts:** `sqlite_database` `nutrition` `food_tracking` `rpc_updates` `thread_pool`

</td>
</tr>
<tr>
<td width="50%">

#### [Personal Shopper Multi-Agent](complex-agents/personal_shopper/personal_shopper.py)
<kbd>advanced</kbd>

E-commerce personal shopper with triage, sales, and returns departments

**Key concepts:** `customer_database` `multi_agent_transfer` `order_management` `customer_identification`

</td>
<td width="50%">

#### [Shopify Voice Shopping Agent](complex-agents/shopify-voice-shopper/shopify.py)
<kbd>advanced</kbd>

Voice shopping assistant for Shopify stores with MCP server integration

**Key concepts:** `mcp_server` `shopify` `dynamic_agent_switching` `rpc_navigation` `fast_llm_response`

</td>
</tr>
<tr>
<td width="50%">

#### [Teleprompter Transcription Agent](complex-agents/teleprompter/cartesia-ink.py)
<kbd>intermediate</kbd>

Real-time teleprompter that sends transcriptions to frontend via RPC

**Key concepts:** `rpc_transcript` `cartesia_stt` `user_input_transcribed` `frontend_communication`

</td>
<td width="50%">

#### [Turn-Taking Detection Agent](complex-agents/turn-taking/agent.py)
<kbd>advanced</kbd>

Agent that exposes end-of-utterance probability for turn-taking research

**Key concepts:** `eou_probability` `turn_detection` `gladia_stt` `multilingual` `rpc_eou_updates`

</td>
</tr>
<tr>
<td width="50%">

#### [Vision-Enabled Agent](complex-agents/vision/agent.py)
<kbd>intermediate</kbd>

Agent with camera vision capabilities using Grok-2 Vision model

**Key concepts:** `video_stream` `grok_vision` `x_ai` `frame_capture` `image_content`

</td>
<td width="50%">
</td>
</tr>
</table>

</details>

<details>
<summary><h3>Drive-Thru System (4 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [Drive-Thru Agent Test Suite](complex-agents/drive-thru/test_agent.py)
<kbd>advanced</kbd>

Comprehensive test suite for drive-thru ordering agent

**Key concepts:** `pytest` `agent_testing` `run_result` `judge_llm` `mock_tools`

</td>
<td width="50%">

#### [Drive-Thru Order Management Tools](complex-agents/drive-thru/tools/management_tools.py)
<kbd>intermediate</kbd>

Order management tools for drive-thru system

**Key concepts:** `order_tools` `rpc_integration` `checkout_flow`

</td>
</tr>
<tr>
<td width="50%">

#### [Drive-Thru Order Placement Tools](complex-agents/drive-thru/tools/order_tools.py)
<kbd>advanced</kbd>

Dynamic tool builders for different order types in drive-thru system

**Key concepts:** `dynamic_tool_generation` `combo_meals` `enum_validation` `size_handling`

</td>
<td width="50%">

#### [Drive-Thru Session Setup](complex-agents/drive-thru/session_setup.py)
<kbd>intermediate</kbd>

Session setup utilities for drive-thru ordering system

**Key concepts:** `session_management` `userdata_initialization` `background_audio_setup`

</td>
</tr>
</table>

</details>

<details>
<summary><h3>Research & Testing (5 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [EXA Deep Researcher Agent Test Suite](complex-agents/exa-deep-researcher/tests/test_agent.py)
<kbd>advanced</kbd>

Test suite for EXA Deep Researcher agent with clarification flow testing

**Key concepts:** `pytest` `agent_testing` `run_result` `judge_llm` `mock_tools`

</td>
<td width="50%">

#### [Basic Agent Test Starter](complex-agents/testing/start_test.py)
<kbd>beginner</kbd>

Simple starting point for testing voice agents with basic greeting validation

**Key concepts:** `pytest` `basic-testing` `getting-started` `agent-greeting`

</td>
</tr>
<tr>
<td width="50%">

#### [Comprehensive Agent Testing](complex-agents/testing/agent_test.py)
<kbd>advanced</kbd>

Complete test suite for voice agents with fixtures, mocks, and conversation flows

**Key concepts:** `pytest` `agent-testing` `function-mocking` `conversation-testing` `fixtures`

</td>
<td width="50%">

#### [Function Calling Test Agent](complex-agents/testing/agent.py)
<kbd>beginner</kbd>

Testing agent with single print_to_console function

**Key concepts:** `function_calling` `console_print` `agent_session_config`

</td>
</tr>
<tr>
<td width="50%">

#### [Testing Test](complex-agents/testing/testing_test.py)
<kbd>beginner</kbd>

Duplicate test file demonstrating basic agent testing patterns

**Key concepts:** `pytest` `test-validation` `duplicate-test` `agent-greeting`

</td>
<td width="50%">
</td>
</tr>
</table>

</details>

<details>
<summary><h3>Hardware & Home Automation (2 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [Pi Zero Transcriber](hardware/pi-zero-transcriber/pi_zero_transcriber.py)
<kbd>beginner</kbd>

Shows how to create a simple transcriber that uses the LiveKit SDK to transcribe audio from the microphone.

**Key concepts:** `hardware` `openai` `deepgram`

</td>
<td width="50%">

#### [Home Automation](home_assistant/homeautomation.py)
<kbd>intermediate</kbd>

Shows how to create an agent that can control home automation devices.

**Key concepts:** `home-automation` `openai` `assemblyai`

</td>
</tr>
</table>

</details>

<details>
<summary><h3>LLM Pipeline Customization (4 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [Interrupt User](pipeline-llm/interrupt_user.py)
<kbd>intermediate</kbd>

Shows how to interrupt the user if they've spoken too much.

**Key concepts:** `pipeline-llm` `openai` `deepgram`

</td>
<td width="50%">

#### [LLM Output Replacement](pipeline-llm/replacing_llm_output.py)
<kbd>intermediate</kbd>

Replaces Deepseek thinking tags with custom messages for TTS

**Key concepts:** `deepseek` `groq` `stream_manipulation` `think_tags` `output_processing`

</td>
</tr>
<tr>
<td width="50%">

#### [LLM-Powered Content Filter](pipeline-llm/llm_powered_content_filter.py)
<kbd>advanced</kbd>

Content filter using a separate LLM for real-time moderation decisions

**Key concepts:** `content_moderation` `dual_llm` `sentence_buffering` `stream_processing`

</td>
<td width="50%">

#### [Simple Content Filter](pipeline-llm/simple_content_filter.py)
<kbd>beginner</kbd>

Basic keyword-based content filter with inline replacement

**Key concepts:** `keyword_filtering` `offensive_terms` `inline_replacement`

</td>
</tr>
</table>

</details>

<details>
<summary><h3>TTS & Audio (4 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [ElevenLabs Change Language](pipeline-tts/changing_language/elevenlabs_change_language.py)
<kbd>intermediate</kbd>

Shows how to use the ElevenLabs TTS model to change the language of the agent.

**Key concepts:** `pipeline-tts` `openai` `deepgram`

</td>
<td width="50%">

#### [Only Greet](pipeline-tts/only_greet.py)
<kbd>beginner</kbd>

Greets the user when they join the room, but doesn't respond to anything else.

**Key concepts:** `pipeline-tts` `openai` `deepgram`

</td>
</tr>
<tr>
<td width="50%">

#### [PlayAI TTS](pipeline-tts/playai_tts.py)
<kbd>intermediate</kbd>

Shows how to use the PlayAI TTS model.

**Key concepts:** `pipeline-tts` `openai` `deepgram`

</td>
<td width="50%">

#### [TTS Comparison](pipeline-tts/tts_comparison/tts_comparison.py)
<kbd>intermediate</kbd>

Switches between different TTS providers using function tools.

**Key concepts:** `pipeline-tts` `openai` `deepgram`

</td>
</tr>
</table>

</details>

<details>
<summary><h3>RAG & Knowledge (2 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [RAG Database Builder](rag/rag_db_builder.py)
<kbd>advanced</kbd>

Builds vector databases for RAG from text documents

**Key concepts:** `annoy_index` `sentence_chunking` `embeddings_generation` `vector_database`

</td>
<td width="50%">

#### [RAG Handler Utility](rag/rag_handler.py)
<kbd>advanced</kbd>

Reusable RAG handler with thinking styles and agent integration

**Key concepts:** `thinking_styles` `rag_enrichment` `agent_registration` `context_injection`

</td>
</tr>
</table>

</details>

<details>
<summary><h3>RPC & State Management (2 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [RPC State Management Agent](rpc/rpc_agent.py)
<kbd>advanced</kbd>

Agent demonstrating RPC communication with comprehensive CRUD state management

**Key concepts:** `rpc` `state-management` `crud-operations` `session-data` `json-handling`

</td>
<td width="50%">

#### [NPC Character State Tracking](tracking_state/npc_character.py)
<kbd>advanced</kbd>

Advanced NPC system with dynamic rapport tracking and conversation state management

**Key concepts:** `npc-interaction` `state-tracking` `rapport-system` `agent-switching` `conversation-flow`

</td>
</tr>
</table>

</details>

<details>
<summary><h3>Telephony (3 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [SIP Lifecycle Management Agent](telephony/sip_lifecycle.py)
<kbd>advanced</kbd>

Advanced SIP agent demonstrating complete call lifecycle management

**Key concepts:** `sip` `call-management` `participant-handling` `call-lifecycle` `function-tools`

</td>
<td width="50%">

#### [Survey Calling Agent](telephony/survey_caller/survey_calling_agent.py)
<kbd>intermediate</kbd>

Automated survey calling agent with CSV data management and response recording

**Key concepts:** `surveys` `data-collection` `csv-handling` `automated-calling` `metadata-processing`

</td>
</tr>
<tr>
<td width="50%">

#### [Warm Handoff Agent](telephony/warm_handoff.py)
<kbd>intermediate</kbd>

Agent demonstrating warm handoff functionality to transfer calls to human agents

**Key concepts:** `call-transfer` `warm-handoff` `sip` `agent-to-human` `function-tools`

</td>
<td width="50%">
</td>
</tr>
</table>

</details>

<details>
<summary><h3>Translation (2 examples)</h3></summary>

<table>
<tr>
<td width="50%">

#### [Pipeline Translator Agent](translators/pipeline_translator.py)
<kbd>intermediate</kbd>

Simple translation pipeline that converts English speech to French

**Key concepts:** `translation` `multilingual` `french` `elevenlabs` `direct-translation`

</td>
<td width="50%">

#### [TTS Translator with Gladia STT](translators/tts_translator.py)
<kbd>advanced</kbd>

Advanced translation system using Gladia STT with code switching and event handling

**Key concepts:** `translation` `gladia-stt` `multilingual` `code-switching` `event-handling`

</td>
</tr>
</table>

</details>

<details>
<summary><h3>Vision (1 example)</h3></summary>

<table>
<tr>
<td width="50%">

#### [Moondream Vision Agent](vision/moondream_vision.py)
<kbd>intermediate</kbd>

Moondream Vision Agent

**Key concepts:** `moondream` `vision`

</td>
<td width="50%">
</td>
</tr>
</table>

</details>

---

## Tips for Exploring

- **Start simple**: Try examples marked as `beginner` first
- **Mix and match**: Many examples use interchangeable components (LLM, STT, TTS, VAD)
- **Check metadata**: Each file includes YAML frontmatter with detailed information
- **Read the index**: Browse `docs/index.yaml` for a complete structured catalog
- **Join the community**: Get help and share your builds on [Discord](https://livekit.io/community)

## Resources

- **[LiveKit Agents Documentation](https://docs.livekit.io/agents/)** - Comprehensive guides and API reference
- **[LiveKit Agents GitHub](https://github.com/livekit/agents)** - SDK source code and issues
- **[LiveKit Cloud](https://cloud.livekit.io)** - Managed infrastructure for production
- **[Discord Community](https://livekit.io/community)** - Get help and connect with other developers

---

<div align="center">

**Built with ❤️ by the LiveKit community**

[Website](https://livekit.io) • [Documentation](https://docs.livekit.io) • [Community](https://livekit.io/community)

</div>
