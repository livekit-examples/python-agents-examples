# xAI Patient Intake

A family-medicine front desk you can call: the agent identifies a caller against a chart,
books and moves appointments, answers practice-policy questions, collects pre-visit
clinical intake, and routes a possible emergency to urgent care — all in one conversation.

The speech pipeline is xAI end to end.

| Stage | Model |
| --- | --- |
| Speech to text | `xai/stt-1` |
| Reasoning | `xai/grok-4.3` (`reasoning_effort="none"`) |
| Text to speech | `xai/tts-1` (voice `carina`) |

> The clinic is an in-memory fake. No real patient data is involved, and nothing here is a
> medical device or a source of medical advice.

## Repository layout

| Directory | Description |
| --- | --- |
| `patient-intake-agent` | Python worker: one agent, one conversation, eight typed tools over an in-memory practice. |
| `frontend` | Next.js app that dispatches the worker and renders the conversation, transcript, and tool calls. |

Each directory has its own README with deeper notes on architecture and customization.

## Design

One agent, one conversation, one fixed tool surface — no handoffs, no task framework, no
workflow state machine. The model holds the conversation in its own context and passes
what it has learned to typed tools when it needs to read or change practice state.

| Tool | Purpose |
| --- | --- |
| `read_practice_information` | Read the complete published practice guide |
| `find_open_times` | Search real slots using typed patient and scheduling facts |
| `book_appointment` | Register a new patient when necessary and book their chosen slot |
| `manage_appointment` | List, cancel, or reschedule an existing appointment |
| `take_message` | Route a refill, results, billing, referral, nurse, or records request |
| `update_insurance` | Save details from a current insurance card |
| `record_previsit_intake` | Save one completed set of pre-visit answers |
| `record_emergency_escalation` | Record a possible emergency and end ordinary work |

Every tool re-verifies identity from its arguments rather than trusting remembered state,
so a caller can book a visit, report a symptom, and update insurance in any order without
a phase machine deciding what is allowed next.

Practice policy stays out of the prompt: `patient-intake-agent/src/clinic/practice_info/`
holds the published guide as Markdown, and one argument-free tool returns all of it,
leaving interpretation to the model instead of a category table.

## Quick start

1. **Configure LiveKit**
   - Create or reuse a LiveKit Cloud project.
   - Grab `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET`.
   - The agent registers as `xai-patient-intake`; the frontend's dispatch allowlist in
     `frontend/app/api/agent/connection_details/route.ts` maps to that name.

2. **Run the agent**

   ```bash
   cd complex-agents/xai-patient-intake/patient-intake-agent
   uv sync
   cp .env.example .env.local   # add your three LiveKit values
   uv run python src/agent.py console   # talk to it in the terminal, no browser needed
   uv run python src/agent.py dev       # or register the worker for the frontend
   ```

3. **Run the frontend**

   ```bash
   cd ../frontend
   pnpm install
   cp .env.example .env.local   # the same three values
   pnpm dev
   ```

   Visit http://localhost:3000/patient-intake and click the card. The route mints a token
   with an explicit agent dispatch, so the worker joins the room the visitor just created.

4. **Try these**
   - *"What are your hours?"* → `read_practice_information`
   - *"I'd like to book an appointment"* → `find_open_times`, then `book_appointment`
   - *"I need a refill on my lisinopril"* → `take_message`

## Tests

```bash
cd patient-intake-agent
uv run pytest tests/unit -q
```

The unit tests assert the exact eight tools assembled in production and exercise booking,
rescheduling, message routing, intake, and emergency handling against the in-memory clinic
without touching the network.
