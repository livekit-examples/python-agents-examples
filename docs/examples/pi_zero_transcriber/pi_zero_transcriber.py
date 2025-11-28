"""
---
title: Pi Zero Transcriber
category: hardware
tags: [hardware, deepgram]
difficulty: beginner
description: Shows how to create a simple transcriber that uses the LiveKit SDK to transcribe audio from the microphone.
demonstrates:
  - Using the LiveKit SDK to transcribe audio from the microphone.
  - Displaying the transcribed text on a Pirate Audio display on a Raspberry Pi Zero 2 W.
---
"""

from dotenv import load_dotenv
from livekit.agents import JobContext, JobProcess, AgentServer, cli, Agent, AgentSession, inference
from livekit.plugins import deepgram

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import st7789
import textwrap

load_dotenv()

SPI_SPEED_MHZ = 20
screen = st7789.ST7789(
    rotation=90,
    port=0,
    cs=1,
    dc=9,
    backlight=13,
    spi_speed_hz=SPI_SPEED_MHZ * 1000 * 1000
)
width = screen.width
height = screen.height

image = Image.new("RGB", (240, 240), (0, 0, 0))
draw = ImageDraw.Draw(image)

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)

def show_startup_screen():
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
    draw.text((10, 10), "LiveKit", font=title_font, fill=(255, 255, 255))
    draw.text((10, 40), "Transcription", font=title_font, fill=(255, 255, 255))
    draw.text((10, 80), "Starting...", font=font, fill=(200, 200, 200))
    screen.display(image)

def display_transcription(text):
    draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
    draw.text((10, 10), "Transcription", font=title_font, fill=(255, 255, 255))

    y_position = 50
    wrapped_text = textwrap.wrap(text, width=26)

    max_lines = 9
    display_lines = wrapped_text[-max_lines:] if len(wrapped_text) > max_lines else wrapped_text

    for line in display_lines:
        draw.text((10, y_position), line, font=font, fill=(200, 200, 200))
        y_position += 20

    screen.display(image)

server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: JobContext):
    show_startup_screen()

    current_transcript = ""
    last_transcript = ""

    session = AgentSession(
        stt=deepgram.STT(),
    )

    @session.on("user_input_transcribed")
    def on_transcript(transcript):
        nonlocal current_transcript, last_transcript

        if transcript.is_final:
            current_transcript += " " + transcript.transcript
            current_transcript = current_transcript.strip()

            with open("user_speech_log.txt", "a") as f:
                f.write(f"{transcript.transcript}\n")
        else:
            last_transcript = transcript.transcript

        display_text = current_transcript
        if not transcript.is_final and last_transcript:
            display_text += " " + last_transcript

        display_transcription(display_text)

    await session.start(
        agent=Agent(
            instructions="You are a helpful assistant that transcribes user speech to text."
        ),
        room=ctx.room
    )
    await ctx.connect()

if __name__ == "__main__":
    try:
        cli.run_app(server)
    except KeyboardInterrupt:
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
        screen.display(image)
        print("\nExiting transcriber")
