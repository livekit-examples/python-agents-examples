"""
---
title: Third-Party Metrics Exporter
category: metrics
tags: [metrics_export, flask_server, all_metrics_types, async_http, event_handlers]
difficulty: advanced
description: Exports all metric types to third-party server via HTTP
demonstrates:
  - Complete metrics collection (LLM, STT, TTS, EOU, VAD)
  - Event handler registration for all metric types
  - Async HTTP requests to metrics server
  - JSON serialization of metrics data
  - Error handling for network requests
  - Comprehensive metrics tracking
---
"""

import logging
import asyncio
import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, vad
from livekit.agents.metrics import LLMMetrics, STTMetrics, TTSMetrics, EOUMetrics, VADMetrics
from livekit.agents.voice import Agent, AgentSession
from livekit.agents.voice.room_io import RoomInputOptions
from livekit.plugins import deepgram, openai, silero

# Configure logging
logger = logging.getLogger("combined-metrics")
logger.setLevel(logging.INFO)

# Reduce log level for HTTP-related libraries
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Configure the metrics server URL
METRICS_SERVER_URL = os.getenv("METRICS_SERVER_URL", "http://localhost:5001") 

class CombinedMetricsAgent(Agent):
    """
    A comprehensive agent that tracks all metrics: LLM, STT, TTS, and VAD.
    """
    def __init__(self) -> None:
        # Initialize components
        llm = openai.LLM(model="gpt-4o-mini")
        stt = deepgram.STT()
        tts = openai.TTS()
        silero_vad = silero.VAD.load()
        
        super().__init__(
            instructions="You are Alloy, a helpful assistant that demonstrates comprehensive metrics tracking.",
            stt=stt,
            llm=llm,
            tts=tts,
            vad=silero_vad,
        )
        
        # Set up event handlers for all metric types
        
        # LLM metrics
        def llm_metrics_wrapper(metrics: LLMMetrics):
            asyncio.create_task(self.on_llm_metrics_collected(metrics))
        llm.on("metrics_collected", llm_metrics_wrapper)
        
        # STT metrics
        def stt_metrics_wrapper(metrics: STTMetrics):
            asyncio.create_task(self.on_stt_metrics_collected(metrics))
        stt.on("metrics_collected", stt_metrics_wrapper)
        
        # EOU metrics
        def eou_metrics_wrapper(metrics: EOUMetrics):
            asyncio.create_task(self.on_eou_metrics_collected(metrics))
        stt.on("eou_metrics_collected", eou_metrics_wrapper)
        
        # TTS metrics
        def tts_metrics_wrapper(metrics: TTSMetrics):
            asyncio.create_task(self.on_tts_metrics_collected(metrics))
        tts.on("metrics_collected", tts_metrics_wrapper)
        
        # VAD metrics
        def vad_metrics_wrapper(event: vad.VADEvent):
            asyncio.create_task(self.on_vad_event(event))
        silero_vad.on("metrics_collected", vad_metrics_wrapper)

    async def send_metrics_to_server(self, metric_type: str, data: dict) -> None:
        """
        Send metrics data to the Flask server
        """
        endpoint = f"{METRICS_SERVER_URL}/metrics/{metric_type}"
        try:
            # Use asyncio to run blocking request in a threadpool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, 
                lambda: requests.post(endpoint, json=data, timeout=2)
            )
        except Exception as e:
            raise e

    async def on_llm_metrics_collected(self, metrics: LLMMetrics) -> None:
        # Create a dictionary of metrics data
        metrics_data = {
            "type": metrics.type,
            "label": metrics.label,
            "request_id": metrics.request_id,
            "timestamp": metrics.timestamp if isinstance(metrics.timestamp, (int, float)) else metrics.timestamp.isoformat() if metrics.timestamp else None,
            "duration": metrics.duration,
            "ttft": metrics.ttft,
            "cancelled": metrics.cancelled,
            "completion_tokens": metrics.completion_tokens,
            "prompt_tokens": metrics.prompt_tokens,
            "total_tokens": metrics.total_tokens,
            "tokens_per_second": metrics.tokens_per_second
        }
        
        # Send metrics to server
        await self.send_metrics_to_server("llm", metrics_data)

    async def on_stt_metrics_collected(self, metrics: STTMetrics) -> None:
        # Create a dictionary of metrics data
        metrics_data = {
            "type": metrics.type,
            "label": metrics.label,
            "request_id": metrics.request_id,
            "timestamp": metrics.timestamp if isinstance(metrics.timestamp, (int, float)) else metrics.timestamp.isoformat() if metrics.timestamp else None,
            "duration": metrics.duration,
            "speech_id": metrics.speech_id,
            "error": str(metrics.error) if metrics.error else None,
            "streamed": metrics.streamed,
            "audio_duration": metrics.audio_duration
        }
        
        # Send metrics to server
        await self.send_metrics_to_server("stt", metrics_data)

    async def on_eou_metrics_collected(self, metrics: EOUMetrics) -> None:
        # Create a dictionary of metrics data
        metrics_data = {
            "type": metrics.type,
            "label": metrics.label,
            "timestamp": metrics.timestamp if isinstance(metrics.timestamp, (int, float)) else metrics.timestamp.isoformat() if metrics.timestamp else None,
            "end_of_utterance_delay": metrics.end_of_utterance_delay,
            "transcription_delay": metrics.transcription_delay,
            "speech_id": metrics.speech_id,
            "error": str(metrics.error) if metrics.error else None
        }
        
        # Send metrics to server
        await self.send_metrics_to_server("eou", metrics_data)

    async def on_tts_metrics_collected(self, metrics: TTSMetrics) -> None:
        # Create a dictionary of metrics data
        metrics_data = {
            "type": metrics.type,
            "label": metrics.label,
            "request_id": metrics.request_id,
            "timestamp": metrics.timestamp if isinstance(metrics.timestamp, (int, float)) else metrics.timestamp.isoformat() if metrics.timestamp else None,
            "ttfb": metrics.ttfb,
            "duration": metrics.duration,
            "audio_duration": metrics.audio_duration,
            "cancelled": metrics.cancelled,
            "characters_count": metrics.characters_count,
            "streamed": metrics.streamed,
            "speech_id": metrics.speech_id,
            "error": str(metrics.error) if metrics.error else None
        }
        
        # Send metrics to server
        await self.send_metrics_to_server("tts", metrics_data)

    async def on_vad_event(self, event: vad.VADEvent) -> None:        
        # Create a dictionary of metrics data
        metrics_data = {
            "type": event.type,
            "timestamp": event.timestamp if isinstance(event.timestamp, (int, float)) else event.timestamp.isoformat() if event.timestamp else None,
            "idle_time": event.idle_time,
            "inference_duration_total": event.inference_duration_total,
            "inference_count": event.inference_count,
            "speech_id": event.speech_id,
            "error": str(event.error) if event.error else None
        }
        
        # Send metrics to server
        await self.send_metrics_to_server("vad", metrics_data)


async def entrypoint(ctx: JobContext):
    session = AgentSession()

    await session.start(
        agent=CombinedMetricsAgent(),
        room=ctx.room,
        room_input_options=RoomInputOptions(),
    )


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint)
    ) 