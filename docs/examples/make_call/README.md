---
title: Outbound Calling Agent
category: telephony
tags: [telephony, outbound-calls, survey, ice-cream-preference]
difficulty: beginner
description: Agent that makes outbound calls to ask about ice cream preferences
demonstrates:
  - Outbound call agent configuration
  - Goal-oriented conversation flow
  - Focused questioning strategy
  - Brief and direct interaction patterns
  - Automatic greeting generation
---

This example Agent that makes outbound calls to ask about ice cream preferences.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  ```
- Install dependencies:
  ```bash
  pip install "livekit-agents[silero]" python-dotenv
  ```

## Run it

```bash
python make_call.py
```

## How it works

- Outbound call agent configuration
- Goal-oriented conversation flow
- Focused questioning strategy
- Brief and direct interaction patterns
- Automatic greeting generation

## Full example

```python
import asyncio
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parents[3] / '.env')

# Set up logging
logger = logging.getLogger("make-call")
logger.setLevel(logging.INFO)

# Configuration
room_name = "my-room"
agent_name = "test-agent"
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

async def make_call(phone_number):
    """Create a dispatch and add a SIP participant to call the phone number"""
    lkapi = api.LiveKitAPI()
    
    # Create agent dispatch
    logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")
    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name, room=room_name, metadata=phone_number
        )
    )
    logger.info(f"Created dispatch: {dispatch}")
    
    # Create SIP participant to make the call
    if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
        logger.error("SIP_OUTBOUND_TRUNK_ID is not set or invalid")
        return
    
    logger.info(f"Dialing {phone_number} to room {room_name}")
    
    try:
        # Create SIP participant to initiate the call
        sip_participant = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                room_name=room_name,
                sip_trunk_id=outbound_trunk_id,
                sip_call_to=phone_number,
                participant_identity="phone_user",
            )
        )
        logger.info(f"Created SIP participant: {sip_participant}")
    except Exception as e:
        logger.error(f"Error creating SIP participant: {e}")
    
    # Close API connection
    await lkapi.aclose()

async def main():
    # Replace with the actual phone number including country code
    phone_number = "+1231231231"
    await make_call(phone_number)

if __name__ == "__main__":
    asyncio.run(main())
```
