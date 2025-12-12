---
title: RPC State Management Agent
category: rpc
tags: [rpc, state-management, crud-operations, session-data, json-handling]
difficulty: advanced
description: Agent demonstrating RPC communication with comprehensive CRUD state management
demonstrates:
  - RPC payload extraction and JSON parsing
  - Session-based CRUD operations (Create, Read, Update, Delete)
  - State management with UUID-based object tracking
  - RPC method registration and error handling
  - Function tools integrated with RPC state
  - Structured error responses and logging
style: two-column
---

This example Agent demonstrating RPC communication with comprehensive CRUD state management.

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

<!-- {% step %} -->
<!-- {% instructions %} -->
## Load environment, logging, and session state model

Set up environment loading, logging, and the session data container used to store RPC-managed objects.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, RunContext, function_tool, RoomOutputOptions
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("rpc-state-agent")
logger.setLevel(logging.INFO)
```
<!-- {% added %} -->
```python
@dataclass
class UserSessionData:
    """Store user session data with CRUD operations."""
    data_objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def create_object(self, object_type: str, object_data: Dict[str, Any]) -> str:
        object_id = str(uuid.uuid4())
        data_container = {
            "id": object_id,
            "type": object_type,
            "created_at": "2025-05-02T09:00:00Z",
            "data": object_data
        }
        self.data_objects[object_id] = data_container
        return object_id

    def read_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        return self.data_objects.get(object_id)

    def update_object(self, object_id: str, update_data: Dict[str, Any]) -> bool:
        if object_id in self.data_objects:
            self.data_objects[object_id]["data"].update(update_data)
            self.data_objects[object_id]["updated_at"] = "2025-05-02T09:30:00Z"
            return True
        return False

    def delete_object(self, object_id: str) -> bool:
        if object_id in self.data_objects:
            del self.data_objects[object_id]
            return True
        return False

    def list_objects(self, object_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        if object_type:
            return {k: v for k, v in self.data_objects.items() if v["type"] == object_type}
        return self.data_objects
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Define the RPC-enabled agent

Create an agent with function tools that perform CRUD over shared session state while configuring STT, LLM, TTS, and VAD.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, RunContext, function_tool, RoomOutputOptions
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("rpc-state-agent")
logger.setLevel(logging.INFO)


@dataclass
class UserSessionData:
    """Store user session data with CRUD operations."""
    data_objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def create_object(self, object_type: str, object_data: Dict[str, Any]) -> str:
        object_id = str(uuid.uuid4())
        data_container = {
            "id": object_id,
            "type": object_type,
            "created_at": "2025-05-02T09:00:00Z",
            "data": object_data
        }
        self.data_objects[object_id] = data_container
        return object_id

    def read_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        return self.data_objects.get(object_id)

    def update_object(self, object_id: str, update_data: Dict[str, Any]) -> bool:
        if object_id in self.data_objects:
            self.data_objects[object_id]["data"].update(update_data)
            self.data_objects[object_id]["updated_at"] = "2025-05-02T09:30:00Z"
            return True
        return False

    def delete_object(self, object_id: str) -> bool:
        if object_id in self.data_objects:
            del self.data_objects[object_id]
            return True
        return False

    def list_objects(self, object_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        if object_type:
            return {k: v for k, v in self.data_objects.items() if v["type"] == object_type}
        return self.data_objects
```
<!-- {% added %} -->
```python
class RPCStateAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are an agent that manages state through RPC calls
                and also through function calls.

                You can create, read, update, and delete data objects.

                Available functions:
                - create_note: Create a new note
                - update_note: Update an existing note
                - read_note: Read a note by ID
                - list_notes: List all available notes
                - delete_note: Delete a note by ID
            """,
            stt=inference.STT(
                model="deepgram/nova-3-general"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
        )

    @function_tool
    async def create_note(self, context: RunContext[UserSessionData], title: str, content: str):
        userdata = context.userdata
        note_data = {"title": title, "content": content}
        note_id = userdata.create_object("note", note_data)
        return f"Created note '{title}' with ID: {note_id}"

    @function_tool
    async def read_note(self, context: RunContext[UserSessionData], note_id: str):
        userdata = context.userdata
        note = userdata.read_object(note_id)
        if not note:
            return f"Note with ID {note_id} not found."
        note_data = note["data"]
        return f"Note: {note_data['title']}\n\n{note_data['content']}"

    @function_tool
    async def update_note(self, context: RunContext[UserSessionData],
                         note_id: str, title: Optional[str], content: Optional[str]):
        userdata = context.userdata
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if content is not None:
            update_data["content"] = content
        if not update_data:
            return "No updates provided."
        success = userdata.update_object(note_id, update_data)
        if not success:
            return f"Note with ID {note_id} not found."
        return f"Updated note with ID: {note_id}"

    @function_tool
    async def list_notes(self, context: RunContext[UserSessionData]):
        userdata = context.userdata
        notes = userdata.list_objects("note")
        if not notes:
            return "No notes found."
        response = "Available notes:\n\n"
        for note_id, note in notes.items():
            note_data = note["data"]
            response += f"- {note_data['title']} (ID: {note_id})\n"
        return response

    @function_tool
    async def delete_note(self, context: RunContext[UserSessionData], note_id: str):
        userdata = context.userdata
        success = userdata.delete_object(note_id)
        if not success:
            return f"Note with ID {note_id} not found."
        return f"Deleted note with ID: {note_id}"
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

<!-- {% step %} -->
<!-- {% instructions %} -->
## Register RPC handler and run the app

Connect to the room, register the RPC method, start the session, and launch the worker.
<!-- {% /instructions %} -->

<!-- {% stepCode %} -->
```python
import logging
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, Agent, AgentSession, inference, RunContext, function_tool, RoomOutputOptions
from livekit.plugins import silero

load_dotenv()

logger = logging.getLogger("rpc-state-agent")
logger.setLevel(logging.INFO)


@dataclass
class UserSessionData:
    """Store user session data with CRUD operations."""
    data_objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def create_object(self, object_type: str, object_data: Dict[str, Any]) -> str:
        object_id = str(uuid.uuid4())
        data_container = {
            "id": object_id,
            "type": object_type,
            "created_at": "2025-05-02T09:00:00Z",
            "data": object_data
        }
        self.data_objects[object_id] = data_container
        return object_id

    def read_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        return self.data_objects.get(object_id)

    def update_object(self, object_id: str, update_data: Dict[str, Any]) -> bool:
        if object_id in self.data_objects:
            self.data_objects[object_id]["data"].update(update_data)
            self.data_objects[object_id]["updated_at"] = "2025-05-02T09:30:00Z"
            return True
        return False

    def delete_object(self, object_id: str) -> bool:
        if object_id in self.data_objects:
            del self.data_objects[object_id]
            return True
        return False

    def list_objects(self, object_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        if object_type:
            return {k: v for k, v in self.data_objects.items() if v["type"] == object_type}
        return self.data_objects


class RPCStateAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""
                You are an agent that manages state through RPC calls
                and also through function calls.

                You can create, read, update, and delete data objects.

                Available functions:
                - create_note: Create a new note
                - update_note: Update an existing note
                - read_note: Read a note by ID
                - list_notes: List all available notes
                - delete_note: Delete a note by ID
            """,
            stt=inference.STT(
                model="deepgram/nova-3-general"
            ),
            llm=inference.LLM(
                model="openai/gpt-5-mini",
                provider="openai",
            ),
            tts=inference.TTS(
                model="cartesia/sonic-3",
                voice="9626c31c-bec5-4cca-baa8-f8ba9e84c8bc",
            ),
            vad=silero.VAD.load()
        )

    @function_tool
    async def create_note(self, context: RunContext[UserSessionData], title: str, content: str):
        userdata = context.userdata
        note_data = {"title": title, "content": content}
        note_id = userdata.create_object("note", note_data)
        return f"Created note '{title}' with ID: {note_id}"

    @function_tool
    async def read_note(self, context: RunContext[UserSessionData], note_id: str):
        userdata = context.userdata
        note = userdata.read_object(note_id)
        if not note:
            return f"Note with ID {note_id} not found."
        note_data = note["data"]
        return f"Note: {note_data['title']}\n\n{note_data['content']}"

    @function_tool
    async def update_note(self, context: RunContext[UserSessionData],
                         note_id: str, title: Optional[str], content: Optional[str]):
        userdata = context.userdata
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if content is not None:
            update_data["content"] = content
        if not update_data:
            return "No updates provided."
        success = userdata.update_object(note_id, update_data)
        if not success:
            return f"Note with ID {note_id} not found."
        return f"Updated note with ID: {note_id}"

    @function_tool
    async def list_notes(self, context: RunContext[UserSessionData]):
        userdata = context.userdata
        notes = userdata.list_objects("note")
        if not notes:
            return "No notes found."
        response = "Available notes:\n\n"
        for note_id, note in notes.items():
            note_data = note["data"]
            response += f"- {note_data['title']} (ID: {note_id})\n"
        return response

    @function_tool
    async def delete_note(self, context: RunContext[UserSessionData], note_id: str):
        userdata = context.userdata
        success = userdata.delete_object(note_id)
        if not success:
            return f"Note with ID {note_id} not found."
        return f"Deleted note with ID: {note_id}"
```
<!-- {% added %} -->
```python
async def entrypoint(ctx: JobContext):
    await ctx.connect()
    userdata = UserSessionData()
    session = AgentSession[UserSessionData](userdata=userdata)
    agent = RPCStateAgent()

    participant = await ctx.wait_for_participant()
    logger.info(f"Participant {participant.identity} joined")

    async def handle_client_state_operation(rpc_data):
        try:
            logger.info(f"Received client state operation: {rpc_data}")
            payload_str = rpc_data.payload
            payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str

            operation = payload.get("operation", "unknown")
            object_type = payload.get("object_type", "unknown")
            object_id = payload.get("object_id")
            object_data = payload.get("data", {})

            result = {"status": "success", "operation": operation, "message": ""}

            if operation == "create":
                new_id = userdata.create_object(object_type, object_data)
                result["object_id"] = new_id
                result["message"] = f"Created {object_type} with ID: {new_id}"
            elif operation == "read":
                if not object_id:
                    result["status"] = "error"
                    result["message"] = "Missing object_id for read operation"
                else:
                    obj = userdata.read_object(object_id)
                    if obj:
                        result["object"] = obj
                        result["message"] = f"Retrieved {object_type} with ID: {object_id}"
                    else:
                        result["status"] = "error"
                        result["message"] = f"Object with ID {object_id} not found"
            elif operation == "update":
                if not object_id:
                    result["status"] = "error"
                    result["message"] = "Missing object_id for update operation"
                else:
                    success = userdata.update_object(object_id, object_data)
                    if success:
                        result["message"] = f"Updated {object_type} with ID: {object_id}"
                    else:
                        result["status"] = "error"
                        result["message"] = f"Object with ID {object_id} not found"
            elif operation == "delete":
                if not object_id:
                    result["status"] = "error"
                    result["message"] = "Missing object_id for delete operation"
                else:
                    success = userdata.delete_object(object_id)
                    if success:
                        result["message"] = f"Deleted {object_type} with ID: {object_id}"
                    else:
                        result["status"] = "error"
                        result["message"] = f"Object with ID {object_id} not found"
            elif operation == "list":
                objects = userdata.list_objects(object_type if object_type != "unknown" else None)
                result["objects"] = objects
                result["count"] = len(objects)
                result["message"] = f"Listed {len(objects)} {object_type} objects"
            else:
                result["status"] = "error"
                result["message"] = f"Unknown operation: {operation}"

            return json.dumps(result)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error for payload: {e}")
            return json.dumps({"status": "error", "message": f"Invalid JSON: {str(e)}"})
        except Exception as e:
            logger.error(f"Error handling client state operation: {e}")
            return json.dumps({"status": "error", "message": str(e)})

    logger.info("Registering RPC method: agent.state")
    ctx.room.local_participant.register_rpc_method("agent.state", handle_client_state_operation)

    await session.start(
        agent=agent,
        room=ctx.room,
        room_output_options=RoomOutputOptions(audio_enabled=True),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
```
<!-- {% /added %} -->
<!-- {% /stepCode %} -->
<!-- {% /step %}-->

## Run it

```bash
python rpc_agent.py console
```

## How it works

- RPC payload extraction and JSON parsing
- Session-based CRUD operations (Create, Read, Update, Delete)
- State management with UUID-based object tracking
- RPC method registration and error handling
- Function tools integrated with RPC state
- Structured error responses and logging
