"""
---
title: Note Taking Assistant
category: complex-agents
tags: [complex-agents, cerebras, deepgram]
difficulty: intermediate
description: Shows how to use the Note Taking Assistant.
demonstrates:
  - Using the Note Taking Assistant.
---
"""
import base64
import os
import logging
import asyncio
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli, metrics
from livekit.agents.voice import Agent, AgentSession, MetricsCollectedEvent
from livekit.agents.llm import ChatContext, ChatMessage
from livekit.plugins import openai, silero, deepgram
from livekit.agents.telemetry import set_tracer_provider
from typing import List

load_dotenv(dotenv_path=Path(__file__).parent.parent.parent / '.env')
usage_collector = metrics.UsageCollector()
logger = logging.getLogger("note_taking_assistant")
logger.setLevel(logging.INFO)

def setup_langfuse(
    host: str | None = None, public_key: str | None = None, secret_key: str | None = None
):
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    public_key = public_key or os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = secret_key or os.getenv("LANGFUSE_SECRET_KEY")
    host = host or os.getenv("LANGFUSE_HOST")

    if not public_key or not secret_key or not host:
        raise ValueError("LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST must be set")

    langfuse_auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{host.rstrip('/')}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"

    trace_provider = TracerProvider()
    trace_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    set_tracer_provider(trace_provider)

class NoteTakingAssistant:
    def __init__(self, ctx: JobContext):
        self.transcriptions: List[str] = []
        self.current_notes: str = ""
        self.note_update_task = None
        # Keep a running copy of the full transcript text
        self.full_transcript: str = ""
        # Remember the last transcription snippet sent to the frontend to avoid duplicates
        self._last_transcription_sent: str = ""
        # Create LLM instance once with Cerebras
        self.llm = openai.LLM.with_cerebras(model="gpt-oss-120b")
        # Store context for RPC communication
        self.ctx = ctx

    def build_display_transcript(self, partial: str | None = None, max_sentences: int = 3) -> str:
        """Return a trimmed transcript preview for the frontend."""
        segments: List[str] = []
        if self.full_transcript.strip():
            segments.append(self.full_transcript.strip())
        if partial and partial.strip():
            segments.append(partial.strip())

        combined = " ".join(segments).strip()
        if not combined:
            return ""

        sentences = [match.group().strip() for match in re.finditer(r'[^.!?]+[.!?]?', combined)]
        if not sentences:
            sentences = [combined]

        recent = sentences[-max_sentences:]
        return " ".join(recent).strip()

    async def update_notes(self, transcript: str):
        """Send the full transcript to Cerebras and update notes"""
        if not transcript.strip():
            logger.info("Skipping note update because transcript is empty")
            return
        try:
            # Send to LLM for processing
            prompt = f"""
                You are a note-taking assistant for a voice-based meeting between a doctor and a patient. You will get a transcript of what is being said, and your job is to take notes.
                Current Notes:
                {self.current_notes if self.current_notes else "(No notes yet)"}

                Transcript So Far:
                {transcript}

                Instructions:
                You should try to track:
                - Chief complaints
                - History of present illness
                - Past medical history

                Only add headers for this information if it is explicitly discussed in the transcription.
                If it is not discussed, do not add any headers for that topic.

                - Integrate the new information into the existing notes if there is any information that should be included.
                - Your job is to capture the spirit of the conversation and the key points that are being discussed, but you don't need to
                include every single thing that is said
                - Never add any information that is not in the transcription.
                - Never add notes about things that should be "confirmed" or "asked" to the patient that haven't been discussed.
                - Your job is exclusively to capture what has been discussed, not keep track of what SHOULD be discussed.
                - Only ever add information that is explicitly discussed in the transcription.
                - Keep the notes organized and structured
                - Return the complete set of notes. If no update is required, repeat the existing notes verbatim.

                Updated Notes:
            """

            ctx = ChatContext([
                ChatMessage(
                    type="message",
                    role="system",
                    content=["""
                             You are an intelligent note-taking medical assistant that creates well-organized, comprehensive notes from patient & doctor transcriptions.
                                - Never add any information that is not in the transcription.
                                - Never add notes about things that should be "confirmed" or "asked" to the patient that haven't been discussed.
                                - Your job is exclusively to capture what has been discussed, not keep track of what SHOULD be discussed.
                             """]
                ),
                ChatMessage(
                    type="message",
                    role="user",
                    content=[prompt]
                )
            ])
            
            response = ""
            async with self.llm.chat(chat_ctx=ctx) as stream:
                async for chunk in stream:
                    if not chunk:
                        continue
                    content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                    if content:
                        response += content
            
            self.current_notes = response.strip()
            
            # Send updated notes to frontend via RPC
            await self.send_notes_to_frontend()
            
        except Exception as e:
            logger.error(f"Error updating notes: {e}")
    
    async def send_notes_to_frontend(self):
        """Send current notes and transcriptions to frontend via RPC"""
        try:
            # Get remote participants
            remote_participants = list(self.ctx.room.remote_participants.values())
            if not remote_participants:
                logger.info("No remote participants found to send notes")
                return
            
            # Send to the first remote participant (the frontend)
            client_participant = remote_participants[0]
            
            # Send notes via RPC
            await self.ctx.room.local_participant.perform_rpc(
                destination_identity=client_participant.identity,
                method="receive_notes",
                payload=json.dumps({
                    "notes": self.current_notes,
                    "transcriptions": self.transcriptions,
                    "timestamp": asyncio.get_event_loop().time()
                })
            )
            logger.info(f"Sent notes to frontend ({client_participant.identity})")
        except Exception as e:
            logger.error(f"Error sending notes via RPC: {e}")
    
    async def send_transcription_to_frontend(self, transcription: str):
        """Send the current transcript to frontend via RPC"""
        if not transcription:
            return
        if transcription == self._last_transcription_sent:
            return
        previous_sent = self._last_transcription_sent
        self._last_transcription_sent = transcription
        try:
            # Get remote participants
            remote_participants = list(self.ctx.room.remote_participants.values())
            if not remote_participants:
                logger.info("No remote participants found to send transcription")
                self._last_transcription_sent = previous_sent
                return
            
            # Send to the first remote participant (the frontend)
            client_participant = remote_participants[0]
            
            # Send transcription via RPC
            await self.ctx.room.local_participant.perform_rpc(
                destination_identity=client_participant.identity,
                method="receive_transcription",
                payload=json.dumps({
                    "transcription": transcription,
                    "timestamp": asyncio.get_event_loop().time()
                })
            )
            logger.info(f"Sent transcription to frontend: {transcription[:50]}...")
        except Exception as e:
            self._last_transcription_sent = previous_sent
            logger.error(f"Error sending transcription via RPC: {e}")
    
    async def generate_diagnosis(self, notes: str) -> str:
        """Generate a diagnosis based on the current notes"""
        try:
            prompt = f"""
                You are a medical diagnostic assistant. Based on the following medical notes from a patient consultation, 
                provide potential diagnoses and recommendations.
                
                Medical Notes:
                {notes}
                
                Please provide:
                1. **Possible Diagnoses**: List the most likely diagnoses based on the symptoms and history
                2. **Differential Diagnoses**: Other conditions to consider
                3. **Recommended Tests**: Suggest appropriate diagnostic tests if needed
                4. **Treatment Considerations**: Initial treatment approaches to consider
                5. **Follow-up Recommendations**: When and why to follow up
                
                IMPORTANT: This is for educational purposes only and should not replace professional medical judgment.
                Always recommend consulting with healthcare professionals for actual medical advice.
                
                Format your response in clear markdown with headers and bullet points.
            """
            
            ctx = ChatContext([
                ChatMessage(
                    type="message",
                    role="system",
                    content=["""You are a knowledgeable medical diagnostic assistant. Provide thorough, 
                             evidence-based assessments while always emphasizing that your analysis is for 
                             educational purposes and should not replace professional medical consultation."""]
                ),
                ChatMessage(
                    type="message",
                    role="user",
                    content=[prompt]
                )
            ])
            
            response = ""
            async with self.llm.chat(chat_ctx=ctx) as stream:
                async for chunk in stream:
                    if not chunk:
                        continue
                    content = getattr(chunk.delta, 'content', None) if hasattr(chunk, 'delta') else str(chunk)
                    if content:
                        response += content
            
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating diagnosis: {e}")
            return f"Error generating diagnosis: {str(e)}"

async def entrypoint(ctx: JobContext):
    setup_langfuse()  # set up the langfuse tracer

    session = AgentSession()
    
    # Create the agent
    agent = Agent(
        instructions="""
            You are a note-taking assistant.
        """,
        stt=deepgram.STTv2(eager_eot_threshold=0.5),
        vad=silero.VAD.load()
        )

    # Create note-taking assistant
    note_assistant = NoteTakingAssistant(ctx)

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        logger.info(f"Transcript received: {transcript}")
        fragment = transcript.transcript.strip()
        if not fragment:
            return

        if transcript.is_final:
            note_assistant.transcriptions.append(fragment)
            if note_assistant.full_transcript:
                note_assistant.full_transcript = f"{note_assistant.full_transcript} {fragment}"
            else:
                note_assistant.full_transcript = fragment

            display_text = note_assistant.build_display_transcript()
            asyncio.create_task(
                note_assistant.send_transcription_to_frontend(display_text)
            )

            logger.info(f"Transcript updated: {fragment}")

            if note_assistant.note_update_task and not note_assistant.note_update_task.done():
                note_assistant.note_update_task.cancel()

            note_assistant.note_update_task = asyncio.create_task(
                note_assistant.update_notes(note_assistant.full_transcript)
            )
        else:
            display_text = note_assistant.build_display_transcript(partial=fragment)
            asyncio.create_task(
                note_assistant.send_transcription_to_frontend(display_text)
            )
    
    @session.on("metrics_collected")
    def _on_metrics_collected(ev: MetricsCollectedEvent):
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    logger.info("Note-taking assistant started. Listening for transcriptions...")

    await session.start(
        agent=agent,
        room=ctx.room
    )
    
    # Register RPC handler for diagnosis requests after session starts
    async def handle_diagnosis_request(rpc_invocation):
        """Handle diagnosis request from frontend"""
        try:
            payload = json.loads(rpc_invocation.payload)
            notes = payload.get("notes", "")
            
            if not notes:
                return json.dumps({"error": "No notes provided for diagnosis"})
            
            # Generate diagnosis
            diagnosis = await note_assistant.generate_diagnosis(notes)
            
            # Send diagnosis back to frontend
            remote_participants = list(ctx.room.remote_participants.values())
            if remote_participants:
                client_participant = remote_participants[0]
                await ctx.room.local_participant.perform_rpc(
                    destination_identity=client_participant.identity,
                    method="receive_diagnosis",
                    payload=json.dumps({
                        "diagnosis": diagnosis,
                        "timestamp": asyncio.get_event_loop().time()
                    })
                )
            
            return json.dumps({"success": True})
        except Exception as e:
            logger.error(f"Error handling diagnosis request: {e}")
            return json.dumps({"error": str(e)})
    
    # Register the RPC method
    ctx.room.local_participant.register_rpc_method("request_diagnosis", handle_diagnosis_request)

    ctx.add_shutdown_callback(log_usage)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
