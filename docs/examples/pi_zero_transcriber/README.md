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

This example shows how to create a real-time speech transcription agent that runs on Raspberry Pi Zero 2 W hardware and displays transcribed text on a Pirate Audio display using LiveKit's voice agents.

## Features

- **Hardware Integration**: Runs directly on Raspberry Pi Zero 2 W
- **LCD Display Output**: Shows transcriptions on Pirate Audio ST7789 240x240 display
- **Real-time Transcription**: Displays both interim and final transcription results
- **Automatic Text Wrapping**: Wraps long text to fit the small screen
- **Scrolling Display**: Shows the most recent 9 lines of transcribed text
- **Persistent Logging**: Saves all transcriptions to a local text file

## Hardware Requirements

- Raspberry Pi Zero 2 W
- Pirate Audio board with ST7789 240x240 display
- USB or I2S microphone
- MicroSD card (8GB or larger)
- Power supply

## Prerequisites

- Raspberry Pi OS (32-bit or 64-bit)
- Python 3.10+
- Pirate Audio libraries installed
- Add a `.env` in this directory with your credentials:
  ```
  LIVEKIT_URL=your_livekit_url
  LIVEKIT_API_KEY=your_api_key
  LIVEKIT_API_SECRET=your_api_secret
  DEEPGRAM_API_KEY=your_deepgram_key
  ```
- Install system dependencies:
  ```bash
  sudo apt-get update
  sudo apt-get install python3-pip python3-pil python3-numpy
  sudo pip install st7789
  ```
- Install Python dependencies:
  ```bash
  pip install livekit-agents python-dotenv livekit-plugins-deepgram
  ```

## Load environment and set up the display

Initialize the ST7789 display with the correct rotation for Pirate Audio and create drawing surfaces.

```python
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
```

## Create display helper functions

Define functions to show the startup screen and render transcription text with automatic wrapping and scrolling.

```python
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
```

## Define the AgentServer and rtc session

Create the server and define the entrypoint that sets up transcription handling with both interim and final results.

```python
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
```

## Run the server with cleanup

Start the agent server and handle keyboard interrupts by clearing the display on exit.

```python
if __name__ == "__main__":
    try:
        cli.run_app(server)
    except KeyboardInterrupt:
        draw.rectangle((0, 0, width, height), fill=(0, 0, 0))
        screen.display(image)
        print("\nExiting transcriber")
```

## Run it

Run directly on the Raspberry Pi:

```bash
python pi_zero_transcriber.py dev
```

The LCD will show "LiveKit Transcription Starting..." and then begin displaying transcribed speech.

## How it works

1. The agent starts and displays a startup screen on the LCD.
2. Connects to a LiveKit room for audio processing.
3. Audio from the microphone is captured and sent to Deepgram STT.
4. As speech is detected, interim transcriptions appear on screen in real-time.
5. Final transcriptions are appended to the display and saved to `user_speech_log.txt`.
6. The display shows up to 9 lines of wrapped text, with older text scrolling off.
7. On exit, the display is cleared gracefully.

## Full example

```python
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
```
