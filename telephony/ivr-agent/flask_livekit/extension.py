from flask import request, jsonify, current_app
from livekit import api
from livekit.protocol.sip import CreateSIPParticipantRequest
import random
import string
import asyncio

class LiveKit(object):
    def __init__(self, app=None):
        self.app = app
        self.api_key = None
        self.api_secret = None
        self.host = None
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the LiveKit extension with the given Flask app."""
        self.api_key = app.config.get('LIVEKIT_API_KEY')
        self.api_secret = app.config.get('LIVEKIT_API_SECRET')
        self.host = app.config.get('LIVEKIT_HOST')

        if not all([self.api_key, self.api_secret, self.host]):
            raise api.LiveKitConfigError("Missing required LiveKit configuration. Please check your config.")

        # Register routes
        app.add_url_rule('/api/generate-token', 'livekit_generate_token',
                         self.generate_token, methods=['POST'])
        app.add_url_rule('/api/create-room', 'livekit_create_room',
                         self.create_room, methods=['POST'])
        app.add_url_rule('/api/call', 'livekit_initiate_call',
                         self.initiate_call, methods=['POST'])

    async def create_sip_participant(self, phone_number, room_name, identity, task):
        """Create a SIP participant using LiveKitAPI."""
        print(f"Creating SIP participant for {phone_number} in room {room_name} with identity {identity}")
        livekit_api = api.LiveKitAPI(self.host, self.api_key, self.api_secret)
        try:
            response = await livekit_api.sip.create_sip_participant(
                api.CreateSIPParticipantRequest(
                    sip_trunk_id=current_app.config.get('SIP_TRUNK_ID'),
                    sip_call_to=phone_number,
                    room_name=room_name,
                    participant_identity=identity,
                    participant_name="SIP Caller",
                    participant_attributes={
                        "task": task,
                    }
                )
            )
            print(f"Response: {response}")
            await livekit_api.aclose()
            return response
        except Exception as e:
            await livekit_api.aclose()
            raise e

    def generate_token(self):
        """Generate a LiveKit access token for a participant."""
        data = request.json
        room_name = data.get("room_name")
        participant_identity = data.get("identity")

        if not room_name or not participant_identity:
            return jsonify({"error": "Missing roomName or identity"}), 400

        token = api.AccessToken() \
            .with_identity(participant_identity) \
            .with_name(participant_identity) \
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
            )).to_jwt()

        return jsonify({"token": token})

    def create_room(self):
        """Create a new LiveKit room."""
        data = request.json
        room_name = data.get("room_name")

        if not room_name:
            return jsonify({"error": "Missing room_name"}), 400

        client = api.RoomServiceClient(self.host, self.api_key, self.api_secret)
        try:
            room = client.create_room(name=room_name)
            return jsonify({"room": room.to_dict()})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    def initiate_call(self):
        """Initiate a call and create a room for it with a SIP participant."""
        data = request.json
        phone_number = data.get("phone_number")
        room_name = data.get("room_name")
        task = data.get("task")
        
        if not phone_number or not room_name or not task:
            return jsonify({"error": "Phone number, room name, and task are required"}), 400
        
        try:
            print(f"Phone number: {phone_number}, Room: {room_name}, Task: {task}")
            
            # Generate identity for SIP participant
            identity = f"sip_{phone_number}"
            # Create SIP participant using asyncio.run()
            result = asyncio.run(self.create_sip_participant(phone_number, room_name, identity, task))
            
            return jsonify({
                "status": "success",
                "message": f"Call initiated to {phone_number} in room {room_name}",
                "result": {
                    "sip_response": result.to_dict() if hasattr(result, 'to_dict') else str(result)
                }
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500 