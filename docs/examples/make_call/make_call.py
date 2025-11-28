"""
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
"""

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
