"""
---
title: MCP Server
category: mcp
tags: [mcp, openai, deepgram]
difficulty: beginner
description: Shows how to create an MCP server that can be used to control a LiveKit room.
demonstrates:
  - Creating an MCP server that can be used to control a LiveKit room.
---
"""
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os
import asyncio
import concurrent.futures
from livekit import api
from livekit.protocol import room as room_proto
from livekit.protocol.models import DataPacket
import json
from pathlib import Path
from functools import wraps
from dotenv import load_dotenv
import aiohttp

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

mcp = FastMCP("LiveKit MCP")

def run_async(coroutine):
    """
    Helper function to run a coroutine either in the current loop or a new one
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coroutine)
                return future.result()
        else:
            return loop.run_until_complete(coroutine)
    except RuntimeError:
        return asyncio.run(coroutine)

async def with_livekit_api(api_func):
    """Wrapper to ensure proper cleanup of LiveKit API sessions"""
    session = aiohttp.ClientSession()
    try:
        lkapi = api.LiveKitAPI(session=session)
        return await api_func(lkapi)
    finally:
        await session.close()

async def fetch_livekit_rooms():
    """
    List all rooms asynchronously
    """
    async def _fetch(lkapi):
        rooms_response = await lkapi.room.list_rooms(room_proto.ListRoomsRequest(names=[]))
        return [{"room_name": room.name} for room in rooms_response.rooms]

    return await with_livekit_api(_fetch)

async def delete_livekit_room(room_name: str):
    """
    Delete a room asynchronously
    """
    async def _delete(lkapi):
        delete_request = room_proto.DeleteRoomRequest(room=room_name)
        await lkapi.room.delete_room(delete_request)
        return True

    return await with_livekit_api(_delete)

async def fetch_room_participants(room_name: str):
    """
    List all participants in a room asynchronously
    """
    async def _fetch(lkapi):
        list_request = room_proto.ListParticipantsRequest(room=room_name)
        participants_response = await lkapi.room.list_participants(list_request)
        return [
            {
                "identity": participant.identity,
                "name": participant.name,
                "state": participant.state,
                "joined_at": participant.joined_at,
                "metadata": participant.metadata,
                "sid": participant.sid
            }
            for participant in participants_response.participants
        ]

    return await with_livekit_api(_fetch)

async def send_chat_to_room(room_name: str, message: str, sender_name: str = "System", destination_identities: list = None):
    """
    Send a chat message to a room asynchronously
    """
    async def _send(lkapi):
        chat_payload = {
            "message": message,
            "sender": sender_name,
            "timestamp": int(asyncio.get_event_loop().time() * 1000)
        }

        data = json.dumps(chat_payload).encode('utf-8')

        send_request = room_proto.SendDataRequest(
            room=room_name,
            data=data,
            kind=DataPacket.Kind.RELIABLE,
            topic="chat"
        )

        if destination_identities:
            send_request.destination_identities.extend(destination_identities)

        await lkapi.room.send_data(send_request)
        return True

    return await with_livekit_api(_send)

@mcp.tool()
def generate_token(identity: str, name: str, room: str) -> str:
    """
    Generate a LiveKit access token

    Args:
        identity: Unique identifier for the participant
        name: Display name of the participant
        room: Name of the room to join

    Returns:
        JWT token string
    """
    token = api.AccessToken(
        os.getenv('LIVEKIT_API_KEY'),
        os.getenv('LIVEKIT_API_SECRET')
    ).with_identity(identity) \
     .with_name(name) \
     .with_grants(api.VideoGrants(
        room_join=True,
        room=room,
    ))

    return token.to_jwt()

@mcp.tool()
async def list_rooms() -> dict:
    """
    List all rooms
    """
    return {"result": await fetch_livekit_rooms()}

@mcp.tool()
def delete_room(room: str) -> bool:
    """
    Delete a room by name

    Args:
        room: Name of the room to delete

    Returns:
        True if successful
    """
    return run_async(delete_livekit_room(room))

@mcp.tool()
def list_participants(room: str) -> list[dict]:
    """
    List all participants in a room

    Args:
        room: Name of the room to list participants from

    Returns:
        List of participant information dictionaries
    """
    return run_async(fetch_room_participants(room))

@mcp.tool()
def send_chat(room: str, message: str, sender: str = "System", recipients: list = None) -> bool:
    """
    Send a chat message to a room

    Args:
        room: Name of the room to send the message to
        message: The chat message to send
        sender: Name of the sender (default: "System")
        recipients: List of participant identities to send to (default: None, which means all participants)

    Returns:
        True if successful
    """
    return run_async(send_chat_to_room(room, message, sender, recipients))

@mcp.tool()
def generate_join_link(room: str, identity: str = "anonymous", name: str = "Anonymous") -> str:
    """
    Generate a LiveKit join link

    Args:
        room: Name of the room to join
        identity: Unique identifier for the participant (default: "anonymous")
        name: Display name of the participant (default: "Anonymous")

    Returns:
        URL string to join the LiveKit room
    """
    token = generate_token(identity, name, room)

    livekit_url = os.getenv('LIVEKIT_URL')

    join_url = f"https://meet.livekit.io/custom?liveKitUrl={livekit_url}&token={token}"

    return join_url

if __name__ == "__main__":
    mcp.run(transport="sse")
