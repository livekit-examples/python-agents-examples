---
title: Outbound Calling Script
category: telephony
tags: [telephony, sip, outbound-calls]
difficulty: beginner
description: Script that makes outbound calls via LiveKit Telephony using the LiveKit API
demonstrates:
  - Creating agent dispatches via the API
  - Dialing outbound numbers via SIP trunks
  - LiveKit API client usage
---

This example shows how to place an outbound call via LiveKit Telephony. The script creates an agent dispatch, then dials a number through a SIP trunk to connect the caller into the agent's room. This is not an agent itself, but a utility script that triggers an agent and connects a phone call to it.

## Prerequisites

- Add a `.env` in this directory with your LiveKit credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  SIP_OUTBOUND_TRUNK_ID=your_sip_trunk_id
  ```
- Provision a SIP outbound trunk in LiveKit and set `SIP_OUTBOUND_TRUNK_ID`
- Install dependencies:
  ```bash
  pip install livekit-api dotenv
  ```

## Load configuration and logging

Load environment variables and set up logging for call status tracking.

```python
import asyncio
import os
import logging
from dotenv import load_dotenv
from livekit import api

load_dotenv()

logger = logging.getLogger("make-call")
logger.setLevel(logging.INFO)
```

## Configure room, agent, and trunk

Set the room name, agent dispatch target, and outbound trunk ID pulled from the environment.

```python
room_name = "my-room"
agent_name = "test-agent"
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
```

## Create the agent dispatch and dial

Use the LiveKit API client to create a dispatch (which starts your agent in the room) and then create a SIP participant to dial the phone number into that room.

```python
async def make_call(phone_number):
    lkapi = api.LiveKitAPI()

    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name, room=room_name, metadata=phone_number
        )
    )

    if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
        logger.error("SIP_OUTBOUND_TRUNK_ID is not set or invalid")
        return

    await lkapi.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=room_name,
            sip_trunk_id=outbound_trunk_id,
            sip_call_to=phone_number,
            participant_identity="phone_user",
        )
    )

    await lkapi.aclose()
```

## Run the script with a number

Provide a phone number (with country code) and run the async entrypoint.

```python
async def main():
    phone_number = "+1231231231"
    await make_call(phone_number)

if __name__ == "__main__":
    asyncio.run(main())
```

## Run it

```console
python make_call.py
```

## How it works

1. An agent dispatch starts the target agent in the specified room.
2. A SIP participant is created via the outbound trunk to dial the user's phone number.
3. Once connected, the caller and agent are in the same LiveKit room.
4. Close the API client after the call is set up.

## Full example

```python
import asyncio
import os
import logging
from dotenv import load_dotenv
from livekit import api

load_dotenv()

logger = logging.getLogger("make-call")
logger.setLevel(logging.INFO)

room_name = "my-room"
agent_name = "test-agent"
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")

async def make_call(phone_number):
    """Create a dispatch and add a SIP participant to call the phone number"""
    lkapi = api.LiveKitAPI()

    logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")
    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name, room=room_name, metadata=phone_number
        )
    )
    logger.info(f"Created dispatch: {dispatch}")

    if not outbound_trunk_id or not outbound_trunk_id.startswith("ST_"):
        logger.error("SIP_OUTBOUND_TRUNK_ID is not set or invalid")
        return

    logger.info(f"Dialing {phone_number} to room {room_name}")

    try:
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

    await lkapi.aclose()

async def main():
    phone_number = "+1231231231"
    await make_call(phone_number)

if __name__ == "__main__":
    asyncio.run(main())
```
