import asyncio
import csv
import json
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit import api

load_dotenv()

logger = logging.getLogger("make-survey-calls")
logger.setLevel(logging.INFO)

# Configuration
room_name_prefix = "survey-call-"
agent_name = "survey-agent"
outbound_trunk_id = os.getenv("SIP_OUTBOUND_TRUNK_ID")
csv_file_path = Path(__file__).parent / "survey_data.csv"

async def make_survey_call(phone_number, question, row_index):
    """Create a dispatch and add a SIP participant to call the phone number with survey question"""
    # Create a unique room name for each call using the prefix and row index
    room_name = f"{room_name_prefix}{row_index}"

    # Create metadata as JSON containing all relevant data
    metadata = json.dumps({
        "phone_number": phone_number,
        "question": question,
        "row_index": row_index
    })

    lkapi = api.LiveKitAPI()

    logger.info(f"Creating dispatch for agent {agent_name} in room {room_name}")

    dispatch = await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=agent_name,
            room=room_name,
            metadata=metadata
        )
    )
    logger.info(f"Created dispatch: {dispatch}")
    logger.info(f"Dialing {phone_number} to room {room_name}")

    sip_participant = await lkapi.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=room_name,
            sip_trunk_id=outbound_trunk_id,
            sip_call_to=phone_number,
            participant_identity="phone_user",
        )
    )
    logger.info(f"Created SIP participant: {sip_participant}")

    await lkapi.aclose()
    return True

async def read_csv_data():
    """Read the CSV file and return the data"""
    data = []
    with open(csv_file_path, 'r', newline='') as f:
        reader = csv.reader(f)
        headers = next(reader)  # Skip headers
        for i, row in enumerate(reader):
            if len(row) >= 2:
                data.append({
                    'row_index': i + 1,
                    'phone_number': row[0],
                    'question': row[1],
                    'answer': row[2] if len(row) > 2 else '',
                    'status': row[3] if len(row) > 3 else ''
                })

    return data

async def process_survey_calls():
    """Process all the survey calls in the CSV"""
    # Read the CSV data
    data = await read_csv_data()

    logger.info(f"Found {len(data)} survey calls to make")

    for item in data:
        if item['answer'] or (item['status'] and item['status'] != ''):
            logger.info(f"Skipping row {item['row_index']} as it already has an answer or status")
            continue

        logger.info(f"Processing survey call to {item['phone_number']} with question: {item['question']}")

        await make_survey_call(item['phone_number'], item['question'], item['row_index'])

async def main():
    logger.info("Starting survey calls process")
    if not outbound_trunk_id:
        logger.error("SIP_OUTBOUND_TRUNK_ID is not set. Please add it to your .env file.")
        return
    await process_survey_calls()
    logger.info("Survey calls process completed")

if __name__ == "__main__":
    asyncio.run(main())
