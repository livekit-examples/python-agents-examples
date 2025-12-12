---
title: Home Automation
category: home-automation
tags: [home-automation, openai, deepgram]
difficulty: intermediate
description: Shows how to create an agent that can control home automation devices.
demonstrates:
  - Using function tools to control home automation devices.
  - Using a wake word to trigger the agent.
---

In this recipe you will build a hot-word gated Home Assistant controller. The agent listens for “hey casa”, then forwards your request to Home Assistant function tools to list or control devices.

## Prerequisites

- Python 3.8+, a running Home Assistant instance, and the dependencies in `requirements.txt`
- A `.env` in this directory with:
  ```
  HOMEAUTOMAITON_TOKEN=your_home_assistant_token_here
  HOMEAUTOMATION_URL=http://localhost:8123   # optional, defaults to localhost
  ```
- Install dependencies:
  ```bash
  pip install -r ../requirements.txt
  ```

## Load configuration and logging

Import dotenv and configure logging so you can see wake-word and API activity.

```python
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("home-automation")
logger.setLevel(logging.INFO)
```

## Build the wake-word agent

Use standard STT/LLM/TTS plus Silero VAD. Track whether the wake word has been heard; greet the user by saying you are waiting for it.

```python
WAKE_WORD = "hey casa"

class SimpleAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are a helpful agent that can control home automation devices.
                You can list available devices and control them by turning them on or off.
                When asked about devices, first list what's available and then help control them.
            """,
            stt=inference.STT(model="deepgram/nova-3-general"),
            llm=inference.LLM(model="openai/gpt-5-mini", provider="openai"),
            tts=inference.TTS(model="cartesia/sonic-3", voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"),
            vad=silero.VAD.load()
        )
        self.wake_word_detected = False
        self.wake_word = WAKE_WORD

    async def on_enter(self):
        logger.info(f"Waiting for wake word: '{WAKE_WORD}'")
        self.session.say(f"Waiting for wake word: '{WAKE_WORD}'")
```

## Filter STT events for the wake word

Override `stt_node` to drop transcripts until the wake word appears. After detecting it, pass only the text after the wake word to the LLM, then reset once the utterance ends.

```python
    def stt_node(self, audio: AsyncIterable[str], model_settings: Optional[dict] = None):
        parent_stream = super().stt_node(audio, model_settings)
        if parent_stream is None:
            return None

        async def process_stream():
            async for event in parent_stream:
                if hasattr(event, "type") and str(event.type) == "SpeechEventType.FINAL_TRANSCRIPT" and event.alternatives:
                    transcript = event.alternatives[0].text.lower()
                    cleaned_transcript = re.sub(r"[^\w\s]", "", transcript)
                    cleaned_transcript = " ".join(cleaned_transcript.split())

                    if not self.wake_word_detected:
                        if self.wake_word in cleaned_transcript:
                            self.wake_word_detected = True
                            content_after = cleaned_transcript.split(self.wake_word, 1)[-1].strip()
                            if content_after:
                                event.alternatives[0].text = content_after
                                yield event
                    else:
                        yield event
                        if str(event.type) == "SpeechEventType.END_OF_SPEECH":
                            self.wake_word_detected = False
                elif self.wake_word_detected:
                    yield event

        return process_stream()
```

## Add function tools for Home Assistant

Implement `list_devices` and `control_device` to call the Home Assistant REST API. They validate tokens, fetch device info, and speak errors when needed.

```python
    @function_tool()
    async def list_devices(self) -> List[Dict[str, str]]:
        url = f"{HOMEAUTOMATION_URL}/api/states"
        headers = {"Authorization": f"Bearer {HOMEAUTOMAITON_TOKEN}"}
        response = requests.get(url, headers=headers, timeout=10)
        # filter to lights, switches, binary sensors and return friendly names
```

```python
    @function_tool()
    async def control_device(self, entity_id: str, state: str) -> None:
        # validate state, fetch friendly name, then POST to /api/services/{domain}/turn_on|turn_off
```

## Prevent replies before wake word

If the wake word has not been detected when a user turn ends, raise `StopResponse` to skip LLM/TTS.

```python
    async def on_user_turn_completed(self, chat_ctx, new_message=None):
        if self.wake_word_detected:
            result = await super().on_user_turn_completed(chat_ctx, new_message)
            self.wake_word_detected = False
            return result
        raise StopResponse()
```

## Start the session

Launch the agent; once running, say “hey casa, list devices” or “hey casa, turn on the kitchen light.”

```python
async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=SimpleAgent(),
        room=ctx.room
    )
```

## Run it

```bash
python homeautomation.py start
```

## How it works

1. Agent greets and waits for the wake word.
2. `stt_node` drops transcripts until “hey casa” is heard, then forwards the rest to the LLM.
3. Function tools call Home Assistant APIs to list or control devices.
4. After each utterance, the wake-word gate resets so the agent listens again.

## Troubleshooting

- Ensure `HOMEAUTOMAITON_TOKEN` is valid and Home Assistant is reachable.
- Check logs for HTTP errors; the agent will announce missing tokens or failed requests.
- The wake word is exact string match; adjust `WAKE_WORD` if you need different phrasing.
