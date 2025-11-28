You are an agent that must accomplish the following.

## 1. Migrate the Python file

Migrate the `*.py` agent file to 1.3+ format by following the migration guide in @migration_guides/1_3.md

Key changes:
- Replace `WorkerOptions(entrypoint_fnc=...)` with `AgentServer` + `@server.rtc_session()` decorator
- Move STT/LLM/TTS/VAD from Agent class to `AgentSession` (keep agents lightweight)
- Add VAD prewarming via `server.setup_fnc`
- Add `await ctx.connect()` after `session.start()`
- Fix model names (e.g., `gpt-4.1-mini` → `gpt-5-mini`)
- Remove unused imports
- Remove docstrings from the top of the python files if the partnered markdown already has the same docstring.

**Hint:** There is an example agent that is already migrated in @answer_call/answer_call.py

## 2. Update the README.md

Ensure the `.md` file follows the format shown in @answer_call/README.md.

**Critical:** Every section header MUST have descriptive text explaining what the code does BEFORE showing the code block. Do NOT just put a header followed immediately by a code block.

### Good example:
```markdown
## Prewarm VAD for faster connections

Preload the VAD model once per process. This runs before any sessions start and stores the VAD instance in `proc.userdata` so it can be reused, cutting down on connection latency.

\`\`\`python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
\`\`\`
```

### Bad example:
```markdown
## Prewarm VAD for faster connections

\`\`\`python
def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

server.setup_fnc = prewarm
\`\`\`
```

### README structure requirements:
- **Frontmatter**: Title, category, tags, difficulty, description, demonstrates
- **Intro paragraph**: Brief description of what the example does
- **Prerequisites**: .env setup and pip install command
- **Step-by-step sections**: Each with a header, descriptive text, then code
- **"Run it" section**: How to run with `console` command
- **"How it works" section**: Numbered list explaining the flow
- **"Full example" section**: Complete Python file without docstrings

### Other requirements:
- These are called "examples", not "tutorials", "guides", or "recipes"
- Update tags in frontmatter to match actual providers used (assemblyai, openai, cartesia, etc.)
- Make sure the full example at the end matches the migrated Python file exactly
