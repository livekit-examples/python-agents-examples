# LemonSlice Salary Negotiation Coach

A LiveKit Agents demo integrating the lemonslice plugin to help people practice asking their boss for a raise through interactive role-play sessions.

## Project overview

This demo creates an AI-powered coaching experience where users can practice salary negotiation conversations. The lemonslice avatar acts as a coach, providing real-time feedback and advice as users role-play with AI-powered bosses that have different personalities and negotiation styles.

### Tech stack

**Backend (Agent)**
- LiveKit Agents framework
- lemonslice plugin for avatar
- Deepgram Nova 3 (STT)
- Google Gemini 2.5 Flash (LLM)
- Cartesia Sonic 3 (TTS)
- Python

**Frontend**
- Next.js
- React
- TypeScript
- Tailwind CSS
- LiveKit React components

## Current status

**Overall progress:** Phase 1 complete, Phase 2 complete

### Backend ✅ Phase 1 complete

**Implemented:**
- Three distinct boss personalities with unique voices and avatars
- Boss personality system: Easy (The Encourager), Medium (The Skeptic), Hard (The Busy Executive)
- Complete coaching and roleplay mode switching
- Session state management tracking negotiation flow
- Function tools for coaching intervention (`how_am_i_doing()`, `return_to_roleplay()`)
- 3-minute session timer with automatic wrap-up
- Conversation analysis and feedback in coaching mode
- Boss-specific prompt files with detailed instructions
- STT/LLM/TTS pipeline fully configured with personality-specific settings

**Location:** `/agent/lemonslice-agent.py`, `/agent/prompts/*.yaml`, `/agent/utils.py`

### Frontend ✅ Phase 2 complete

**Implemented:**
- Custom welcome screen with boss personality selection
- Three selectable boss cards (Easy, Medium, Hard)
- Zoom-style session UI with mode indicators
- Real-time mode tracking (roleplay vs coaching)
- Session timer (3-minute countdown)
- "How am I doing?" coaching trigger button
- Visual mode indicators with colored borders
- Custom LemonSlice branding
- Voice-only interface (video/screenshare disabled)

**Location:** `/frontend/`

## Project goals

### Core experience flow

1. **Welcome screen** - User sees introduction and selects a boss personality
2. **Session setup** - Brief coaching tips before starting
3. **Role-play mode** - User practices conversation with selected boss
4. **Coaching interventions** - Coach avatar provides feedback at key moments
5. **Session summary** - Review performance and get actionable advice

### Boss personalities

Three distinct boss types to practice with:

1. **The Encourager**
   - Supportive and open to discussion
   - Good for building confidence
   - Responds positively to clear value demonstrations

2. **The Skeptic**
   - Questions everything
   - Challenges user to defend their worth
   - Pushes back on numbers
   - Good for preparing difficult conversations

3. **The Busy Executive**
   - Impatient and time-constrained
   - Values conciseness
   - Needs quick, compelling arguments
   - Good for practicing elevator pitch style asks

### Coaching strategy

The coach should:
- Recognize conversation patterns (hesitation, weak language, strong arguments)
- Intervene at appropriate moments with advice
- Praise effective techniques
- Suggest alternative approaches when user struggles
- Track key negotiation moments (opening ask, handling objections, closing)

## Implementation plan

### Phase 1: Backend agent intelligence ✅ Complete

- [x] Create boss personality system with distinct prompts
- [x] Implement coaching detection logic (when to intervene)
- [x] Add session state management (track conversation flow)
- [x] Build context switching (role-play mode vs coaching mode)
- [x] Add conversation analysis (detect patterns, strengths, weaknesses)
- [x] Create structured instructions for different scenarios

**Implementation details:**
- Three boss agents (`EasyBossAgent`, `MediumBossAgent`, `HardBossAgent`) each with unique personalities, voices, and avatar configurations
- Function tools: `how_am_i_doing()` for coaching intervention, `return_to_roleplay()` for returning to boss mode
- `UserData` class manages session state including mode, boss type, timing, negotiation phase, and coaching requests
- 3-minute session timer with automatic wrap-up and summary
- YAML prompt files (`easy_boss_prompt.yaml`, `medium_boss_prompt.yaml`, `hard_boss_prompt.yaml`) contain dual-role instructions for both boss and coaching modes
- Dynamic instruction updating via `update_instructions()` for seamless mode switching
- Room attributes broadcast current mode to frontend

### Phase 2: Frontend Zoom-style UI ✅ Complete

- [x] Design Zoom call layout (video tiles, controls)
- [x] Build boss personality selector screen
- [x] Create session setup flow with pre-coaching tips
- [x] Add role-play specific controls
  - [x] "How am I doing?" coaching button
  - [x] End session button
  - [x] Session timer display
- [x] Implement visual indicators for coaching mode vs role-play mode
- [x] Mode-based colored borders (blue for roleplay, green for coaching)
- [x] Top bar mode indicator with animated pulse
- [ ] Add session transcript with annotations (using existing chat transcript)
- [ ] Build session summary view with insights

**Implementation details:**
- Boss personality data in `/frontend/lib/boss-personalities.ts`
- Custom welcome view with three boss selection cards
- Boss type passed via participant attributes to agent
- Real-time mode tracking using `useParticipantAttributes` hook
- Mode indicator component at top of screen
- Session timer with low-time warning (< 60s)
- Coaching button sends chat message to trigger mode switch
- Tile layout responds to mode with dynamic border colors
- Token endpoint updated to accept and pass participant attributes

### Phase 3: Polish and features

- [ ] Add conversation recording/replay
- [ ] Implement performance scoring
- [ ] Create progress tracking across sessions
- [ ] Add practice scenario variations
- [ ] Build tips library
- [ ] Add keyboard shortcuts
- [ ] Responsive design optimization

## Technical notes

### Environment variables needed

```bash
# LemonSlice Configuration
LEMONSLICE_API_KEY=your_lemonslice_api_key
LEMONSLICE_IMAGE_URL=https://your-publicly-accessible-image-url.com/avatar.jpg

# LiveKit Configuration
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
LIVEKIT_URL=wss://your-project.livekit.cloud
```

### Agent running

```bash
cd agent
uv run lemonslice-agent.py dev
```

### Frontend running

```bash
cd frontend
pnpm dev
```

## Development tools and resources

This project uses several tools to ensure all code follows LiveKit best practices and uses the latest documented patterns. All implementation decisions should be based on verified information from these sources.

### Cursor skills (.cursor/skills/)

The `.cursor/skills/` folder contains reference documentation for LiveKit development. These skills provide structured guidance and code examples for different aspects of the LiveKit ecosystem.

**agents-py** - Python agent development
- Location: `.cursor/skills/agents-py/`
- Use when: Building or modifying the Python agent backend
- Covers: AgentSession, Agent class, function tools, STT/LLM/TTS models, turn detection, workflows
- References: agent-session.md, tools.md, models.md, workflows.md, livekit-overview.md

**agents-ui** - React frontend components
- Location: `.cursor/skills/agents-ui/`
- Use when: Building or customizing the React frontend UI
- Covers: AgentSessionProvider, audio visualizers, media controls, chat transcripts, Tailwind customization
- References: components.md, livekit-overview.md

**livekit-cli** - Command-line tools
- Location: `.cursor/skills/livekit-cli/`
- Use when: Managing projects, deploying agents, generating tokens, configuring telephony
- Covers: Project management, agent deployment, token generation, phone number management
- References: project-commands.md, agent-commands.md, telephony-commands.md, livekit-overview.md

**react-hooks** - React hooks for custom UIs
- Location: `.cursor/skills/react-hooks/`
- Use when: Building custom React components that need low-level LiveKit state access
- Covers: Participant hooks, track hooks, room hooks, session hooks, agent hooks, data hooks
- References: participant-hooks.md, track-hooks.md, room-hooks.md, session-hooks.md, agent-hooks.md, data-hooks.md, livekit-overview.md

### LiveKit MCP tools

The LiveKit Model Context Protocol (MCP) server provides direct access to LiveKit documentation, code examples, and best practices. These tools should be used to verify implementation approaches and find current examples.

**Documentation access**
- `mcp_livekit-docs_get_docs_overview` - Get complete docs structure and table of contents
- `mcp_livekit-docs_get_pages` - Fetch specific documentation pages by path
- `mcp_livekit-docs_docs_search` - Search documentation for specific topics

**Code examples and reference**
- `mcp_livekit-docs_get_python_agent_example` - Browse and retrieve Python agent examples from the official repository
- `mcp_livekit-docs_code_search` - Search GitHub code across LiveKit repositories for implementation patterns

**Version and changelog**
- `mcp_livekit-docs_get_changelog` - Get recent changelog entries and releases for LiveKit packages

**Feedback**
- `mcp_livekit-docs_submit_docs_feedback` - Submit feedback on documentation (optional)

### Using these tools effectively

**Before implementing any feature:**
1. Search the LiveKit docs using MCP tools to find official guidance
2. Check relevant Cursor skills for structured examples and patterns
3. Search code examples to see how similar features are implemented
4. Verify model strings, API patterns, and best practices are current

**When modifying agent code:**
- Consult `agents-py` skill references for AgentSession patterns, tool definitions, and model configuration
- Use MCP tools to verify current model strings and plugin configurations
- Search for similar agent examples to understand implementation patterns

**When modifying frontend code:**
- Consult `agents-ui` skill for component usage and customization patterns
- Use `react-hooks` skill when building custom components that need LiveKit state
- Verify component APIs and hook usage with MCP documentation tools
- Follow component usage hierarchy: Agents UI library → shadcn components → custom Tailwind CSS

**When deploying or configuring:**
- Use `livekit-cli` skill for deployment commands and project management
- Verify CLI commands and options with MCP documentation

### Important principles

1. **Never guess** - Always verify implementation approaches using the available tools
2. **Use official patterns** - Follow examples from LiveKit documentation and official repositories
3. **Check for updates** - Use changelog tools to verify you're using current best practices
4. **Cite sources** - While citations aren't required in code, be able to point to documentation or examples that support implementation decisions
5. **Prefer Inference model strings** - Use LiveKit Inference model strings (e.g., `"openai/gpt-4.1-mini"`) as defaults rather than managing individual provider API keys, unless specific custom models are needed
6. **Component usage hierarchy** - When building frontend UI, prioritize components in this order:
   - First: Agents UI library components (whenever possible)
   - Second: shadcn components (when Agents UI doesn't have what you need)
   - Last resort: Custom Tailwind CSS (only when neither of the above options work)

## Design considerations

### Zoom-style UI elements

- Split-screen video layout
- User on left, boss/coach on right
- Bottom control bar (mic, camera, end session)
- Top bar showing current mode (role-play/coaching)
- Side panel for live transcript and tips
- Minimal distractions to focus on practice

### Visual indicators

- Blue border: Role-play mode active
- Green border: Coaching mode active
- Yellow pulse: AI thinking/analyzing
- Notification badges: New advice available

## Open questions

- Should coaching be automatic or user-triggered?
  - Triggered by a button that says How am I doing?
- Should sessions have time limits?
  - 3 minutes then it goes back to the main page

## Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [LemonSlice Plugin](https://docs.livekit.io/agents/plugins/lemonslice/)
- [LiveKit React Components](https://docs.livekit.io/realtime/client-sdks/react/)

## Notes

- This is a demo/proof of concept for the lemonslice integration
- Focus on teaching value for web developer audience
- Keep complexity manageable for tutorial purposes
- Prioritize clear, understandable code over advanced features
