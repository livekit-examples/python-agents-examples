"""
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
---
"""

import logging
import json
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, RoomOutputOptions
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.agents.llm import function_tool
from livekit.plugins import silero

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

logger = logging.getLogger("rpc-state-agent")
logger.setLevel(logging.INFO)

# ====== RPC STATE MANAGEMENT PATTERNS ======
"""
When implementing RPC state management, it's important to understand
the following key patterns:

1. RPC PAYLOAD STRUCTURE:
   - Payloads come wrapped in an RpcInvocationData object
   - You must extract the payload using rpc_data.payload
   - Payloads may be strings (requiring JSON parsing) or already parsed objects

2. STATE MANAGEMENT:
   - Store state in a dedicated data structure (UserSessionData)
   - Use unique IDs to reference objects across the application
   - Implement proper CRUD operations (Create, Read, Update, Delete)
   - Keep track of object metadata (creation time, updates, etc.)

3. ERROR HANDLING:
   - Validate inputs before processing
   - Return structured error responses
   - Log operations for debugging
"""

# ====== Session Data Structure ======

@dataclass
class UserSessionData:
    """Store user session data with CRUD operations."""
    # Dictionary to store data objects by their ID
    data_objects: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def create_object(self, object_type: str, object_data: Dict[str, Any]) -> str:
        """Create a new data object with auto-generated ID."""
        object_id = str(uuid.uuid4())

        # Create a container with metadata and the actual data
        data_container = {
            "id": object_id,
            "type": object_type,
            "created_at": "2025-05-02T09:00:00Z",  # would normally use datetime.now().isoformat()
            "data": object_data
        }

        # Store in the data dictionary. You could put this in longer term storage
        # if you were building a real production application
        self.data_objects[object_id] = data_container
        return object_id

    def read_object(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Read a data object by ID."""
        return self.data_objects.get(object_id)

    def update_object(self, object_id: str, update_data: Dict[str, Any]) -> bool:
        """Update a data object by ID."""
        if object_id in self.data_objects:
            # Merge the update data with the existing data
            self.data_objects[object_id]["data"].update(update_data)
            self.data_objects[object_id]["updated_at"] = "2025-05-02T09:30:00Z"  # would normally use datetime.now()
            return True
        return False

    def delete_object(self, object_id: str) -> bool:
        """Delete a data object by ID."""
        if object_id in self.data_objects:
            del self.data_objects[object_id]
            return True
        return False

    def list_objects(self, object_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """List all objects, optionally filtered by type."""
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
            stt="assemblyai/universal-streaming",
            llm="openai/gpt-4.1-mini",
            tts="cartesia/sonic-2:6f84f4b8-58a2-430c-8c79-688dad597532",
            vad=silero.VAD.load()
        )

    @function_tool
    async def create_note(self, context: RunContext[UserSessionData], title: str, content: str):
        """Create a new note and store it in the session state.

        Args:
            title: The title of the note
            content: The content of the note
        """
        userdata = context.userdata

        # Create note data
        note_data = {
            "title": title,
            "content": content
        }

        # Store the note in session state
        note_id = userdata.create_object("note", note_data)

        return f"Created note '{title}' with ID: {note_id}"

    @function_tool
    async def read_note(self, context: RunContext[UserSessionData], note_id: str):
        """Read a note by its ID.

        Args:
            note_id: The ID of the note to read
        """
        userdata = context.userdata

        # Read the note from session state
        note = userdata.read_object(note_id)

        if not note:
            return f"Note with ID {note_id} not found."

        note_data = note["data"]
        return f"Note: {note_data['title']}\n\n{note_data['content']}"

    @function_tool
    async def update_note(self, context: RunContext[UserSessionData],
                         note_id: str, title: Optional[str], content: Optional[str]):
        """Update a note by its ID.

        Args:
            note_id: The ID of the note to update
            title: New title for the note (can be null to keep existing)
            content: New content for the note (can be null to keep existing)
        """
        userdata = context.userdata

        # Prepare update data
        update_data = {}
        if title is not None:
            update_data["title"] = title
        if content is not None:
            update_data["content"] = content

        if not update_data:
            return "No updates provided."

        # Update the note
        success = userdata.update_object(note_id, update_data)

        if not success:
            return f"Note with ID {note_id} not found."

        return f"Updated note with ID: {note_id}"

    @function_tool
    async def list_notes(self, context: RunContext[UserSessionData]):
        """List all notes currently stored in the session."""
        userdata = context.userdata

        # Get all notes
        notes = userdata.list_objects("note")

        if not notes:
            return "No notes found."

        # Format the response
        response = "Available notes:\n\n"
        for note_id, note in notes.items():
            note_data = note["data"]
            response += f"- {note_data['title']} (ID: {note_id})\n"

        return response

    @function_tool
    async def delete_note(self, context: RunContext[UserSessionData], note_id: str):
        """Delete a note by its ID.

        Args:
            note_id: The ID of the note to delete
        """
        userdata = context.userdata

        # Delete the note
        success = userdata.delete_object(note_id)

        if not success:
            return f"Note with ID {note_id} not found."

        return f"Deleted note with ID: {note_id}"


async def entrypoint(ctx: JobContext):
    # Connect to the room *before* awaiting the participant
    await ctx.connect()

    # Create user session data - this is the shared state container
    userdata = UserSessionData()

    # Create the agent session with userdata
    # This makes the userdata available to the LLM through the RunContext
    # Note the generic type parameter [UserSessionData] which tells the
    # agent session what type of data to expect
    session = AgentSession[UserSessionData](userdata=userdata)
    agent = RPCStateAgent()

    # How session data flows to the LLM:
    # 1. We create userdata and pass it to AgentSession
    # 2. The agent session makes this userdata available to function tools via RunContext
    # 3. Each function tool receives a context parameter: RunContext[UserSessionData]
    # 4. Inside each function, we access userdata with: userdata = context.userdata
    # 5. The RPC handler has direct access to the same userdata instance
    #
    # This creates a shared state between:
    # - LLM function calls (create_note, read_note, etc.)
    # - RPC handler (handle_client_state_operation)
    #
    # So changes made via RPC are visible to the LLM, and changes made by
    # the LLM are visible via RPC.

    # Wait for a participant to join before proceeding
    participant = await ctx.wait_for_participant()
    logger.info(f"Participant {participant.identity} joined")

    # ====== RPC Handler for Client State Operations ======
    """
    RPC handler for managing state operations through RPC calls.

    This handler processes CRUD operations (Create, Read, Update, Delete, List)
    on data objects stored in the agent's session state.

    Example payloads for each operation:

    1. CREATE operation:
    ```json
    {
        "operation": "create",
        "object_type": "note",
        "data": {
            "title": "Meeting Notes",
            "content": "Discussed project timeline and next steps."
        }
    }
    ```

    2. READ operation:
    ```json
    {
        "operation": "read",
        "object_type": "note",
        "object_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    3. UPDATE operation:
    ```json
    {
        "operation": "update",
        "object_type": "note",
        "object_id": "550e8400-e29b-41d4-a716-446655440000",
        "data": {
            "title": "Updated Meeting Notes",
            "content": "Revised timeline and action items."
        }
    }
    ```

    4. DELETE operation:
    ```json
    {
        "operation": "delete",
        "object_type": "note",
        "object_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    5. LIST operation:
    ```json
    {
        "operation": "list",
        "object_type": "note"
    }
    ```

    Each operation returns a structured JSON response with status, message, and
    operation-specific data (e.g., created object ID, read object data, etc.).
    """
    async def handle_client_state_operation(rpc_data):
        try:
            logger.info(f"Received client state operation: {rpc_data}")

            # Extract payload from RpcInvocationData object
            payload_str = rpc_data.payload
            logger.info(f"Extracted payload string: {payload_str}")

            # Parse the JSON payload
            payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
            logger.info(f"Parsed payload data: {payload}")

            # Extract operation details
            operation = payload.get("operation", "unknown")
            object_type = payload.get("object_type", "unknown")
            object_id = payload.get("object_id")
            object_data = payload.get("data", {})

            result = {
                "status": "success",
                "operation": operation,
                "message": ""
            }

            # Process the operation
            if operation == "create":
                # Create a new object
                new_id = userdata.create_object(object_type, object_data)
                result["object_id"] = new_id
                result["message"] = f"Created {object_type} with ID: {new_id}"

            elif operation == "read":
                # Read an object
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
                # Update an object
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
                # Delete an object
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
                # List objects
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

    # ====== Register RPC method ======
    logger.info("Registering RPC method: agent.state")
    ctx.room.local_participant.register_rpc_method(
        "agent.state",
        handle_client_state_operation
    )

    # Start the agent session
    await session.start(
        agent=agent,
        room=ctx.room,
        room_output_options=RoomOutputOptions(
            audio_enabled=True
        )
    )

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
