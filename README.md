# LiveKit Agents Examples

A collection of runnable Python demos and reference applications built with [LiveKit Agents](https://docs.livekit.io/agents/). The repository currently contains **104** examples that cover everything from single-file quickstarts to production-style, multi-agent systems with dedicated frontends.

## What's Inside
- Voice, video, and telephony agents that demonstrate LiveKit's real-time APIs and the `livekit-agents` Python SDK
- Metadata-rich examples – every script now starts with YAML frontmatter (title, category, tags, difficulty, description, demonstrates) so tooling and LLMs can reason about the catalog
- A centralized index (`docs/index.yaml`) that lists every example along with its metadata for fast discovery and automation
- Complex demos that showcase advanced patterns such as multi-agent orchestration, RPC integrations, hardware bridges, benchmarking, and testing utilities

## Discover the Catalog
- Browse `docs/index.yaml` for the complete list of examples, their descriptions, tags, and demonstrated concepts
- Use the frontmatter at the top of each script (inside a triple-quoted string) to inspect metadata directly in the file
- Many larger demos include their own `README.md` with architectural details or frontend instructions

## Getting Started

### Prerequisites
- Python 3.10 or newer
- `pip` (or another Python package manager)
- LiveKit account credentials (`LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET`)
- API keys for the providers you want to exercise (OpenAI, Deepgram, Cartesia, Anthropic, etc.)
- Node.js 18+ and `pnpm` (only required for demos that ship with a web frontend)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/livekit-examples/python-agents-examples.git
   cd python-agents-examples
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\\Scripts\\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Configure Environment Variables
Create a `.env` file at the repository root with your credentials. At a minimum:
```
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret
```
Add provider-specific keys (OpenAI, Deepgram, ElevenLabs, Cartesia, etc.) depending on the examples you plan to run. Many demos read these values via `dotenv`.

## Running Examples

### Console-based demos
Most single-file examples can be launched directly via the CLI helper shipped with `livekit-agents`:
```bash
python basics/listen_and_respond.py console
```
The `console` argument opens an interactive session where you can speak (or type) with the agent. Swap in any other example path as needed.

### Demos with companion frontends
Some complex agents include a frontend (look for directories such as `*-frontend/`). The typical flow is:
```bash
python complex-agents/medical_office_triage/triage.py dev  # starts the backend worker
cd complex-agents/medical_office_triage/medical-office-frontend
pnpm install
pnpm dev
```
Each project-level README documents the exact commands, required env vars, and how the backend and frontend communicate.

## Tips for Exploring
- Use `rg "---" -g"*.py"` to quickly find frontmatter blocks or discover all scripts in a given category
- Many demos demonstrate interchangeable components (LLM, STT, TTS, VAD). Adjust provider classes or configuration to experiment with different vendors
- The `metrics/`, `testing/`, and `benchmarking/` directories provide utilities for measuring latency, load, and agent quality
- `docs/index.yaml` can be consumed by tooling or LLMs to generate curated playlists, search experiences, or documentation

## Additional Resources
- LiveKit Agents documentation: https://docs.livekit.io/agents/
- LiveKit Agents GitHub repository: https://github.com/livekit/agents
- Join the LiveKit community on Discord: https://livekit.io/community
