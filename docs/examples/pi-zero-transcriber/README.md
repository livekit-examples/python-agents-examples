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

# Pi Zero Transcriber Agent

A real-time speech transcription agent that runs on Raspberry Pi Zero 2 W hardware and displays transcribed text on a Pirate Audio display using LiveKit's voice agents.

## Overview

**Pi Zero Transcriber** - A hardware-based voice agent that captures audio from a microphone, transcribes speech in real-time, and displays the text on a small LCD screen attached to a Raspberry Pi Zero 2 W.

## Features

- **Hardware Integration**: Runs directly on Raspberry Pi Zero 2 W
- **LCD Display Output**: Shows transcriptions on Pirate Audio ST7789 240x240 display
- **Real-time Transcription**: Displays both interim and final transcription results
- **Automatic Text Wrapping**: Wraps long text to fit the small screen
- **Scrolling Display**: Shows the most recent 9 lines of transcribed text
- **Persistent Logging**: Saves all transcriptions to a local text file
- **Voice-Enabled**: Built using LiveKit's voice capabilities with support for:
  - Speech-to-Text (STT) using Deepgram
  - Voice Activity Detection (VAD) using default settings

## Hardware Requirements

- Raspberry Pi Zero 2 W
- Pirate Audio board with ST7789 240x240 display
- USB or I2S microphone
- MicroSD card (8GB or larger)
- Power supply

## How It Works

1. The agent starts and displays a startup screen on the LCD
2. Connects to LiveKit room for audio processing
3. Audio from the microphone is captured and sent to Deepgram STT
4. As speech is detected, interim transcriptions appear on screen
5. Final transcriptions are appended to the display and saved to file
6. The display shows up to 9 lines of wrapped text at once
7. Older text scrolls off as new transcriptions arrive

## Prerequisites

- Raspberry Pi OS (32-bit or 64-bit)
- Python 3.10+
- `livekit-agents`>=1.0
- Pirate Audio libraries installed
- LiveKit account and credentials
- API keys for:
  - Deepgram (for speech-to-text)

## Installation

1. Set up your Raspberry Pi Zero 2 W with Raspberry Pi OS

2. Install system dependencies:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-pil python3-numpy
   sudo pip install st7789
   ```

3. Clone the repository and install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the parent directory with your API credentials:
   ```
   LIVEKIT_URL=your_livekit_url
   LIVEKIT_API_KEY=your_api_key
   LIVEKIT_API_SECRET=your_api_secret
   DEEPGRAM_API_KEY=your_deepgram_key
   ```

## Running the Agent

Run directly on the Raspberry Pi:
```bash
python pi_zero_transcriber.py dev
```

The LCD will show "LiveKit Transcription Starting..." and then begin displaying transcribed speech.

## Architecture Details

### Display Configuration

- **Screen**: ST7789 240x240 pixel color LCD
- **Rotation**: 90 degrees for proper Pirate Audio orientation
- **SPI Speed**: 20 MHz for responsive updates
- **Fonts**: DejaVu Sans for readability on small screen

### Text Display Logic

1. Title "Transcription" always shown at top
2. Text wrapped to 26 characters per line
3. Maximum 9 lines displayed (older lines scroll off)
4. Interim results shown in real-time
5. Final results appended to transcript history

### File Logging

All final transcriptions are saved to `user_speech_log.txt` with one utterance per line for later reference or processing.

### Display Management

- Startup screen shown during initialization
- Clean shutdown clears display on exit
- PIL (Python Imaging Library) used for text rendering
- Hardware SPI interface for fast display updates