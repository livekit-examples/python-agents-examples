"""
---
title: Pi Zero Transcriber
category: hardware
tags: [hardware, openai, deepgram]
difficulty: beginner
description: Shows how to create a simple transcriber that uses the LiveKit SDK to transcribe audio from the microphone.
demonstrates:
  - Using the LiveKit SDK to transcribe audio from the microphone.
  - Displaying the transcribed text on a Pirate Audio display on a Raspberry Pi Zero 2 W.
---
"""

from pathlib import Path
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import deepgram
from pathlib import Path

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import st7789
import os
import signal
import time
import textwrap

# Load environment variables
load_dotenv(dotenv_path=Path(__file__).parent.parent / '.env')

# Set up the screen
SPI_SPEED_MHZ = 20
screen = st7789.ST7789(
    rotation=90,   # Needed to display the right way up on Pirate Audio
    port=0,        # SPI port
    cs=1,          # SPI port Chip-select channel
    dc=9,          # BCM pin used for data/command
    backlight=13,
    spi_speed_hz=SPI_SPEED_MHZ * 1000 * 1000
)
width = screen.width
height = screen.height

# Create image for display
image = Image.new("RGB", (240, 240), (0, 0, 0))
draw = ImageDraw.Draw(image)

# Set up font
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)

# Display startup screen
def show_startup_screen():
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
    draw.text((10, 10), "LiveKit", font=title_font, fill=(255, 255, 255))
    draw.text((10, 40), "Transcription", font=title_font, fill=(255, 255, 255))
    draw.text((10, 80), "Starting...", font=font, fill=(200, 200, 200))
    screen.display(image)

# Display transcription text
def display_transcription(text):
    # Clear screen
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
    
    # Add title
    draw.text((10, 10), "Transcription", font=title_font, fill=(255, 255, 255))

    # Wrap and display the transcribed text
    y_position = 50
    wrapped_text = textwrap.wrap(text, width=26)  # Adjust width as needed

    # Display only the most recent lines that fit on screen
    max_lines = 9  # Approximate number of lines that fit
    display_lines = wrapped_text[-max_lines:] if len(wrapped_text) > max_lines else wrapped_text

    for line in display_lines:
        draw.text((10, y_position), line, font=font, fill=(200, 200, 200))
        y_position += 20  # Line spacing

    screen.display(image)

async def entrypoint(ctx: JobContext):
    show_startup_screen()
    session = AgentSession()

    # Keep track of the current transcription
    current_transcript = ""
    last_transcript = ""

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        nonlocal current_transcript, last_transcript
        
        # Update the current transcript
        if transcript.is_final:
            # For final transcripts, update the full text
            current_transcript += " " + transcript.transcript
            current_transcript = current_transcript.strip()
            
            # Save to file
            with open("user_speech_log.txt", "a") as f:
                f.write(f"{transcript.transcript}\n")
        else:
            # For interim results, show the current segment
            last_transcript = transcript.transcript
        
        # Display the combined text (completed transcript + current segment)
        display_text = current_transcript
        if not transcript.is_final and last_transcript:
            display_text += " " + last_transcript

        display_transcription(display_text)

    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that transcribes user speech to text.",
            stt=deepgram.STT()
        ),
        room=ctx.room
    )

if __name__ == "__main__":
    try:
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
    except KeyboardInterrupt:
        # Clear screen on exit
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
        screen.display(image)
        print("\nExiting transcriber")
