"""
Reachy Mini LiveKit Client

This client connects a Reachy Mini robot to a LiveKit room, streaming video and audio,
and provides RPC methods for the agent to control the robot.
"""

import asyncio
import json
import logging
import threading
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import JobContext

from reachy_mini import ReachyMini

logger = logging.getLogger("reachy-client")
logger.setLevel(logging.INFO)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')


def _largest_face(faces):
    """Return (x, y, w, h) of the largest face (by area) or None."""
    if faces is None or len(faces) == 0:
        return None
    # faces rows are (x, y, w, h)
    return max(faces, key=lambda b: int(b[2]) * int(b[3]))


class ReachyMiniClient:
    """Client that connects Reachy Mini to LiveKit room."""
    
    def __init__(self, room: rtc.Room, reachy_mini: ReachyMini):
        self.room = room
        self.reachy_mini = reachy_mini
        self.video_source: Optional[rtc.VideoSource] = None
        self.audio_source: Optional[rtc.AudioSource] = None
        self.video_track: Optional[rtc.LocalVideoTrack] = None
        self.audio_track: Optional[rtc.LocalAudioTrack] = None
        self.running = False
        self.face_cascade = None
        self._face_detection_lock = threading.Lock()
        self._look_at_me_requested = False
        
        # Initialize face detection
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            logger.warning(f"Failed to load face cascade at '{cascade_path}'. Face detection will be disabled.")
            self.face_cascade = None

    async def start(self):
        """Start streaming video and audio to the room."""
        self.running = True
        
        # Get camera resolution from Reachy Mini
        try:
            camera = self.reachy_mini.media.camera
            if camera:
                cam_width, cam_height = camera.resolution  # Returns (width, height)
            else:
                # Default resolution if camera not available
                cam_width, cam_height = 1920, 1080
        except (RuntimeError, AttributeError):
            # Default resolution if camera not initialized
            cam_width, cam_height = 1920, 1080
        
        # Create video source and track with camera resolution
        self.video_source = rtc.VideoSource(cam_width, cam_height)
        self.video_track = rtc.LocalVideoTrack.create_video_track("reachy-camera", self.video_source)
        
        # Create audio source and track
        self.audio_source = rtc.AudioSource(48000, 1)  # 48kHz, mono
        self.audio_track = rtc.LocalAudioTrack.create_audio_track("reachy-microphone", self.audio_source)
        
        # Publish tracks
        await self.room.local_participant.publish_track(
            self.video_track,
            rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_CAMERA)
        )
        await self.room.local_participant.publish_track(
            self.audio_track,
            rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
        )
        
        logger.info("Published video and audio tracks to room")
        
        # Start video streaming task
        asyncio.create_task(self._stream_video())
        
        # Start audio streaming task
        asyncio.create_task(self._stream_audio())
        
        # Register RPC methods
        await self.room.local_participant.register_rpc_method(
            "robot.look_at_me",
            self._handle_look_at_me
        )
        
        logger.info("Registered RPC methods")

    async def stop(self):
        """Stop streaming and cleanup."""
        self.running = False
        if self.video_track:
            await self.room.local_participant.unpublish_track(self.video_track)
        if self.audio_track:
            await self.room.local_participant.unpublish_track(self.audio_track)

    async def _stream_video(self):
        """Stream video frames from Reachy Mini camera to LiveKit."""
        frame_count = 0
        last_fps_time = time.time()
        
        while self.running:
            try:
                frame = self.reachy_mini.media.get_frame()
                if frame is None:
                    await asyncio.sleep(0.033)  # ~30fps
                    continue
                
                # Convert BGR to RGB if needed (OpenCV uses BGR, LiveKit expects RGB)
                if len(frame.shape) == 3 and frame.shape[2] == 3:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    frame_rgb = frame
                
                # Resize frame to match video source resolution
                if frame_rgb.shape[1] != self.video_source.width or frame_rgb.shape[0] != self.video_source.height:
                    frame_rgb = cv2.resize(frame_rgb, (self.video_source.width, self.video_source.height))
                
                # Create VideoFrame - LiveKit expects RGB format
                # Convert numpy array to bytes in RGB format
                frame_bytes = frame_rgb.tobytes()
                video_frame = rtc.VideoFrame(
                    width=self.video_source.width,
                    height=self.video_source.height,
                    data=frame_bytes
                )
                
                # Capture frame
                await self.video_source.capture_frame(video_frame)
                
                # FPS logging
                frame_count += 1
                if time.time() - last_fps_time > 5.0:
                    fps = frame_count / (time.time() - last_fps_time)
                    logger.debug(f"Video streaming FPS: {fps:.1f}")
                    frame_count = 0
                    last_fps_time = time.time()
                
                # Target ~30fps
                await asyncio.sleep(0.033)
                
            except Exception as e:
                logger.error(f"Error streaming video: {e}")
                await asyncio.sleep(0.1)

    async def _stream_audio(self):
        """Stream audio from Reachy Mini microphone to LiveKit."""
        while self.running:
            try:
                # Get audio sample from Reachy Mini
                audio_sample = self.reachy_mini.media.get_audio_sample()
                if audio_sample is None:
                    await asyncio.sleep(0.01)
                    continue
                
                # Convert to numpy array if needed
                if isinstance(audio_sample, np.ndarray):
                    audio_data = audio_sample
                else:
                    audio_data = np.frombuffer(audio_sample, dtype=np.int16)
                
                # Ensure mono and correct sample rate
                if len(audio_data.shape) > 1:
                    audio_data = audio_data[:, 0]  # Take first channel
                
                # Convert to float32 in range [-1, 1]
                if audio_data.dtype != np.float32:
                    audio_data = audio_data.astype(np.float32) / 32768.0
                
                # Create AudioFrame
                audio_frame = rtc.AudioFrame(
                    sample_rate=48000,
                    num_channels=1,
                    samples_per_channel=len(audio_data),
                    data=audio_data.tobytes()
                )
                
                # Capture frame
                await self.audio_source.capture_frame(audio_frame)
                
                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error streaming audio: {e}")
                await asyncio.sleep(0.1)

    async def _handle_look_at_me(self, rpc_data) -> str:
        """Handle RPC call to make robot look at the person."""
        try:
            logger.info("Received look_at_me RPC call")
            
            with self._face_detection_lock:
                self._look_at_me_requested = True
            
            # Try to detect face and look at it
            success = await self._detect_and_look_at_face()
            
            if success:
                return json.dumps({
                    "status": "success",
                    "message": "Robot is now looking at you!"
                })
            else:
                return json.dumps({
                    "status": "error",
                    "message": "No face detected. Please make sure you're visible to the camera."
                })
                
        except Exception as e:
            logger.error(f"Error in look_at_me handler: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    async def _detect_and_look_at_face(self) -> bool:
        """Detect face in camera feed and make robot look at it."""
        if self.face_cascade is None:
            logger.warning("Face detection not available")
            return False
        
        # Get current frame
        frame = self.reachy_mini.media.get_frame()
        if frame is None:
            return False
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
        )
        
        # Find largest face
        largest_face = _largest_face(faces)
        
        if largest_face is None:
            return False
        
        # Get center of face
        x, y, w, h = largest_face
        cx = x + w // 2
        cy = y + h // 2
        
        # Make robot look at the face center
        try:
            self.reachy_mini.look_at_image(cx, cy, duration=0.5)
            logger.info(f"Robot looking at face at ({cx}, {cy})")
            return True
        except Exception as e:
            logger.error(f"Error making robot look at face: {e}")
            return False


async def main():
    """Main entry point for Reachy Mini client."""
    import os
    from livekit import api
    
    # Get LiveKit credentials from environment
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")
    room_name = os.getenv("LIVEKIT_ROOM_NAME", "reachy-mini-room")
    participant_name = os.getenv("LIVEKIT_PARTICIPANT_NAME", "reachy-mini")
    
    if not url or not api_key or not api_secret:
        raise ValueError("LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET must be set")
    
    # Create access token
    token = api.AccessToken(api_key, api_secret) \
        .with_identity(participant_name) \
        .with_name("Reachy Mini Robot") \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
        ))
    
    # Connect to room
    room = rtc.Room()
    await room.connect(url, token.to_jwt())
    logger.info(f"Connected to room: {room_name}")
    
    # Initialize Reachy Mini
    reachy_mini = ReachyMini(media_backend="default")
    logger.info("Initialized Reachy Mini")
    
    # Create and start client
    client = ReachyMiniClient(room, reachy_mini)
    await client.start()
    
    logger.info("Reachy Mini client started. Press Ctrl+C to stop.")
    
    try:
        # Keep running
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Stopping...")
    finally:
        await client.stop()
        await room.disconnect()
        reachy_mini.media_manager.close()
        logger.info("Disconnected")


if __name__ == "__main__":
    asyncio.run(main())

