"""
---
title: Reachy Mini Agent
category: complex-agents
tags: [reachy_mini, robot, vision, grok_vision, rpc, face_detection]
difficulty: intermediate
description: LiveKit agent for controlling Reachy Mini robot with vision capabilities
demonstrates:
  - RPC communication between agent and robot client
  - Vision-enabled agent using Grok-2 Vision
  - Function tools for robot control
  - Remote robot control via LiveKit
---
"""

import asyncio
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext, WorkerOptions, cli, get_job_context
from livekit.agents.llm import function_tool, ImageContent, ChatContext, ChatMessage
from livekit.agents.voice import Agent, AgentSession, RunContext
from livekit.plugins import deepgram, openai, silero, cartesia

logger = logging.getLogger("reachy-mini-agent")
logger.setLevel(logging.INFO)

print(Path(__file__).parent.parent.parent / '.env')
load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')


class ReachyMiniAgent(Agent):
    def __init__(self) -> None:
        self._latest_frame = None
        self._video_stream = None
        self._tasks = []
        self._room = None
        super().__init__(
            instructions="""
                You are an assistant controlling a Reachy Mini robot.
                You can see what the robot's camera sees and control the robot's movements.
                When the user asks you to "look at me" or similar, use the look_at_me function to make the robot look at them.
                Don't use any unpronouncable characters.
            """,
            stt=deepgram.STT(),
            llm=openai.LLM.with_x_ai(model="grok-2-vision", tool_choice=None),
            tts=cartesia.TTS(
                model="sonic-3",
                voice="32b3f3c5-7171-46aa-abe7-b598964aa793",
                emotion="excited",
            ),
            vad=silero.VAD.load()
        )

    async def on_enter(self):
        
        await self.session.generate_reply(
            instructions="Greet the user with a warm welcome and ask what they want Reachy to do?",
        )
        
        self._room = get_job_context().room

        # Find the first video track (if any) from the remote participant (robot)
        if self._room.remote_participants:
            remote_participant = list(self._room.remote_participants.values())[0]
            video_tracks = [
                publication.track
                for publication in list(remote_participant.track_publications.values())
                if publication.track and publication.track.kind == rtc.TrackKind.KIND_VIDEO
            ]
            if video_tracks:
                self._create_video_stream(video_tracks[0])

        # Watch for new video tracks
        @self._room.on("track_subscribed")
        def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
            if track.kind == rtc.TrackKind.KIND_VIDEO:
                self._create_video_stream(track)

    async def on_user_turn_completed(self, turn_ctx: ChatContext, new_message: ChatMessage) -> None:
        # Add the latest video frame, if any, to the new message
        if self._latest_frame:
            new_message.content.append(ImageContent(image=self._latest_frame))
            self._latest_frame = None

    def _create_video_stream(self, track: rtc.Track):
        # Close any existing stream (we only want one at a time)
        if self._video_stream is not None:
            self._video_stream.close()

        # Create a new stream to receive frames
        self._video_stream = rtc.VideoStream(track)
        async def read_stream():
            async for event in self._video_stream:
                # Store the latest frame for use later
                self._latest_frame = event.frame

        # Store the async task
        task = asyncio.create_task(read_stream())
        task.add_done_callback(lambda t: self._tasks.remove(t) if t in self._tasks else None)
        self._tasks.append(task)

    @function_tool
    async def look_at_me(self, ctx: RunContext) -> str:
        """Make the robot look at the person in front of it by detecting their face.
        
        This function triggers the robot to detect faces in its camera feed and look at the largest detected face.
        """
        try:
            # Find the robot participant (remote participant that's not the user)
            if not self._room or not self._room.remote_participants:
                return "Robot not connected. Please ensure the Reachy Mini client is running and connected to the room."

            # Get the first remote participant (should be the robot)
            robot_participant = list(self._room.remote_participants.values())[0]
            
            # Call RPC method on the robot participant
            result = await robot_participant.invoke_rpc_method(
                "robot.look_at_me",
                json.dumps({})
            )
            
            if result:
                result_data = json.loads(result) if isinstance(result, str) else result
                if result_data.get("status") == "success":
                    return f"Robot is now looking at you! {result_data.get('message', '')}"
                else:
                    return f"Failed to look at you: {result_data.get('message', 'Unknown error')}"
            else:
                return "No response from robot. The robot may not be ready."
                
        except Exception as e:
            logger.error(f"Error calling look_at_me RPC: {e}")
            return f"Error: {str(e)}"


async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=ReachyMiniAgent(),
        room=ctx.room
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

