import hashlib
import hmac
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from livekit.api import (
    AccessToken,
    LiveKitAPI,
    RoomAgentDispatch,
    RoomConfiguration,
    VideoGrants,
)
from livekit.protocol.room import ListRoomsRequest
from pydantic import BaseModel

load_dotenv(".env.local")

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY", "")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET", "")
# Shared secret for HMAC identity verification.
# Each customer gets this secret to compute user_hash on their backend.
WIDGET_SECRET = os.getenv("WIDGET_SECRET", "")


def verify_user(user_id: str, user_hash: str) -> bool:
    if not WIDGET_SECRET:
        return True  # No secret configured, skip verification (dev mode)
    expected = hmac.new(
        WIDGET_SECRET.encode(), user_id.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, user_hash)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class TokenRequest(BaseModel):
    user_id: str
    user_hash: str = ""


@app.post("/api/token")
async def get_token(req: TokenRequest):
    if not verify_user(req.user_id, req.user_hash):
        raise HTTPException(status_code=403, detail="Invalid user_hash")

    room_name = f"user-{req.user_id}"

    token = (
        AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        .with_identity(req.user_id)
        .with_grants(VideoGrants(room_join=True, room=room_name))
        .with_room_config(
            RoomConfiguration(
                agents=[
                    RoomAgentDispatch(
                        agent_name="multi-domain-agent",
                        metadata=json.dumps({"user_id": req.user_id}),
                    )
                ],
            ),
        )
        .to_jwt()
    )

    return {"server_url": LIVEKIT_URL, "participant_token": token}


@app.get("/api/room-status")
async def room_status(user_id: str, user_hash: str = ""):
    if not verify_user(user_id, user_hash):
        raise HTTPException(status_code=403, detail="Invalid user_hash")

    room_name = f"user-{user_id}"
    api = LiveKitAPI()
    try:
        res = await api.room.list_rooms(ListRoomsRequest(names=[room_name]))
        return {"active": len(res.rooms) > 0}
    except Exception:
        return {"active": False}
    finally:
        await api.aclose()


# Serve frontend static files
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
