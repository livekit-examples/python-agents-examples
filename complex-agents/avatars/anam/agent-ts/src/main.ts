import {
  type JobContext,
  type JobProcess,
  ServerOptions,
  cli,
  defineAgent,
  inference,
  metrics,
  voice,
} from '@livekit/agents';
import { TrackKind } from '@livekit/rtc-node';
import * as anam from '@livekit/agents-plugin-anam';
import * as livekit from '@livekit/agents-plugin-livekit';
import * as silero from '@livekit/agents-plugin-silero';
import { BackgroundVoiceCancellation } from '@livekit/noise-cancellation-node';
import dotenv from 'dotenv';
import { fileURLToPath } from 'node:url';
import { Agent } from './agent';

/** Canonical sample rate for Anam avatar audio (matches Python plugin). */
const ANAM_SAMPLE_RATE = 24000;

// Load environment variables from a local file.
// Make sure to set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET
// when running locally or self-hosting your agent server.
dotenv.config({ path: '.env.local' });

export default defineAgent({
  prewarm: async (proc: JobProcess) => {
    proc.userData.vad = await silero.VAD.load();
  },
  entry: async (ctx: JobContext) => {
    // Join the room and connect to the user before starting avatar/session
    await ctx.connect();

    // Set up a voice AI pipeline using LiveKit Inference (STT, LLM, TTS)
    const session = new voice.AgentSession({
      stt: new inference.STT({
        model: 'deepgram/nova-3',
        language: 'multi',
      }),

      llm: new inference.LLM({
        model: 'openai/gpt-4o-mini',
      }),

      tts: new inference.TTS({
        model: 'elevenlabs/eleven_turbo_v2_5',
        voice: 'cgSgspJ2msm6clMCkdW9', // Jessica (ElevenLabs)
        sampleRate: 16000, // TTS output; resampled to ANAM_SAMPLE_RATE for avatar
      }),

      // VAD and turn detection are used to determine when the user is speaking and when the agent should respond
      // See more at https://docs.livekit.io/agents/build/turns
      turnDetection: new livekit.turnDetector.MultilingualModel(),
      vad: ctx.proc.userData.vad! as silero.VAD,
      voiceOptions: {
        // Allow the LLM to generate a response while waiting for the end of turn
        preemptiveGeneration: true,
      },
    });

    // To use a realtime model instead of a voice pipeline, use the following session setup instead.
    // (Note: This is for the OpenAI Realtime API. For other providers, see https://docs.livekit.io/agents/models/realtime/))
    // 1. Install '@livekit/agents-plugin-openai'
    // 2. Set OPENAI_API_KEY in .env.local
    // 3. Add import `import * as openai from '@livekit/agents-plugin-openai'` to the top of this file
    // 4. Use the following session setup instead of the version above
    // const session = new voice.AgentSession({
    //   llm: new openai.realtime.RealtimeModel({ voice: 'marin' }),
    // });

    // Metrics collection, to measure pipeline performance
    // For more information, see https://docs.livekit.io/agents/build/metrics/
    const usageCollector = new metrics.UsageCollector();
    session.on(voice.AgentSessionEventTypes.MetricsCollected, (ev) => {
      metrics.logMetrics(ev.metrics);
      usageCollector.collect(ev.metrics);
    });

    const logUsage = async () => {
      const summary = usageCollector.getSummary();
      console.log(`Usage: ${JSON.stringify(summary)}`);
    };

    ctx.addShutdownCallback(logUsage);

    // Start the session first, which initializes the voice pipeline and warms up the models
    await session.start({
      agent: new Agent(),
      room: ctx.room,
      inputOptions: {
        noiseCancellation: BackgroundVoiceCancellation(),
      },
    });

    // Create Anam avatar (Liv) — lip-synced video avatar
    // Must be created AFTER session.start() so it can connect to the audio stream for lip-sync
    const avatar = new anam.AvatarSession({
      personaConfig: {
        name: 'Liv',
        avatarId: '071b0286-4cce-4808-bee2-e642f1062de3',
      },
    });

    // Start the avatar and wait for it to join the room
    await avatar.start(session, ctx.room);

    // Override avatar output with explicit sample rate so the pipeline resamples TTS (16kHz) to
    // Anam's expected 24kHz. The plugin does not pass sampleRate, which causes chipmunk audio.
    session.output.audio = new voice.DataStreamAudioOutput({
      room: ctx.room,
      destinationIdentity: 'anam-avatar-agent',
      sampleRate: ANAM_SAMPLE_RATE,
      waitRemoteTrack: TrackKind.KIND_VIDEO,
    });
    console.log(
      `Anam avatar: TTS 16000Hz -> output ${ANAM_SAMPLE_RATE}Hz (sink sampleRate=${session.output.audio?.sampleRate})`,
    );

    // Greet the patient and begin intake
    session.generateReply({
      instructions:
        "Use the defined opening line, then begin with the full name question.",
    });
  },
});

// Run the agent server
cli.runApp(
  new ServerOptions({
    agent: fileURLToPath(import.meta.url),
    agentName: 'Anam-Demo',
  }),
);
