"use client";

import {
  LiveKitRoom,
  RoomAudioRenderer,
  TrackToggle,
  useRoomContext,
  useVoiceAssistant,
} from "@livekit/components-react";
import { Track } from "livekit-client";
import "@livekit/components-styles";
import { useState } from "react";
import { ResearchPanel } from "@/components/ResearchPanel";
import { Search, Volume2, VolumeX } from "lucide-react";

export default function Home() {
  const [token, setToken] = useState<string>("");
  const [serverUrl, setServerUrl] = useState<string>("");
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string>("");
  const [connecting, setConnecting] = useState(false);

  const connectToRoom = async () => {
    setConnecting(true);
    setError("");
    try {
      const response = await fetch("/api/token", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          identity: "user-" + Date.now(),
        }),
      });
      const data = await response.json();
      if (data.error) {
        setError(data.error);
        setConnecting(false);
        return;
      }
      setToken(data.token);
      setServerUrl(data.serverUrl);
      setConnected(true);
      setError("");
    } catch (err) {
      setError("Failed to connect. Please check your server configuration.");
      console.error(err);
      setConnecting(false);
    }
  };

  if (!connected) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-bg0 p-6">
        <div className="max-w-md w-full bg-bg1 rounded-xl shadow-sm p-8 border border-separator1">
          <div className="flex flex-col items-center gap-6">
            {/* Icon */}
            <div className="w-16 h-16 rounded-full bg-bgAccent1/20 border border-fgAccent1/30 flex items-center justify-center">
              <Search className="w-8 h-8 text-fgAccent1" />
            </div>

            {/* Title */}
            <div className="flex flex-col items-center gap-2 text-center">
              <h1 className="text-xl font-semibold text-fg0">
                Exa + LiveKit Deep Researcher
              </h1>
              <p className="text-sm text-fg3">Voice AI Research Assistant</p>
              <p className="text-xs text-fg4 leading-relaxed mt-2 max-w-sm">
                Demonstrates autonomous deep research with iterative planning,
                real-time UI updates via RPC streaming, and intelligent query
                clarification—showcasing how voice agents can conduct
                comprehensive multi-step research workflows.
              </p>
            </div>

            {/* Local Development Notice */}
            <div className="w-full bg-bgCaution1/20 border border-fgCaution1/30 rounded-lg px-4 py-3">
              <p className="text-xs text-fg2 leading-relaxed text-center">
                <span className="font-semibold text-fgCaution1">
                  Local development:
                </span>{" "}
                Make sure to run the Python agent first with{" "}
                <code className="bg-bg2 px-1.5 py-0.5 rounded text-fgAccent1 font-mono">
                  python agent.py dev
                </code>
              </p>
            </div>

            {/* Documentation Links */}
            <div className="flex items-center gap-4 text-xs">
              <a
                href="https://docs.exa.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="text-fg3 hover:text-fgAccent1 underline transition-colors"
              >
                Exa Docs
              </a>
              <span className="text-separator2">•</span>
              <a
                href="https://docs.livekit.io/agents"
                target="_blank"
                rel="noopener noreferrer"
                className="text-fg3 hover:text-fgAccent1 underline transition-colors"
              >
                LiveKit Agents Docs
              </a>
              <span className="text-separator2">•</span>
              <a
                href="https://livekit.io/join-slack"
                target="_blank"
                rel="noopener noreferrer"
                className="text-fg3 hover:text-fgAccent1 underline transition-colors"
              >
                LiveKit Slack
              </a>
            </div>

            {/* Connect Button */}
            <button
              onClick={connectToRoom}
              disabled={connecting}
              className="w-full bg-fgAccent1 text-bg0 py-3 px-6 rounded-lg hover:bg-fgAccent2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold text-sm"
            >
              {connecting ? "Connecting..." : "Connect to Room"}
            </button>

            {/* Error Message */}
            {error && (
              <div className="w-full text-fgSerious1 text-sm text-center bg-bgSerious1/20 border border-fgSerious1/30 rounded-lg px-4 py-2">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div data-lk-theme="default" className="flex h-screen flex-col bg-bg0">
      <LiveKitRoom
        video={false}
        audio={true}
        token={token}
        serverUrl={serverUrl}
        className="flex-1 flex flex-col"
      >
        <HeaderControls />
        {/* Research Panel */}
        <div className="flex-1 overflow-hidden min-h-0">
          <ResearchPanel />
        </div>

        {/* Audio Renderer */}
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}

function HeaderControls() {
  const room = useRoomContext();
  const { audioTrack } = useVoiceAssistant();

  // Derive mute state from publication properties
  const agentMuted = audioTrack?.publication
    ? !(audioTrack.publication.isSubscribed && audioTrack.publication.isEnabled)
    : false;

  const toggleAgentMute = async () => {
    if (!room || !audioTrack?.publication) return;

    // Get the remote participant and their audio track publication
    const remoteParticipants = Array.from(room.remoteParticipants.values());
    const agentParticipant = remoteParticipants.find((p) => p.isAgent);

    if (agentParticipant) {
      // Find the audio track publication
      const audioPublications = Array.from(
        agentParticipant.audioTrackPublications.values()
      );
      const audioPublication = audioPublications.find(
        (pub) => pub.trackSid === audioTrack.publication.trackSid
      );

      if (audioPublication) {
        // Use setEnabled() for subscriber-side mute (proper LiveKit API)
        // Toggle: if currently enabled, disable it; if disabled, enable it
        audioPublication.setEnabled(agentMuted);
      }
    }
  };

  return (
    <div className="border-b border-separator1 bg-bg1 px-6 py-3 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold text-fg0">Exa + LiveKit Deep Researcher</h1>
        <div className="h-4 w-px bg-separator2" />
        <span className="text-sm text-fg3">Voice AI Research Assistant</span>
      </div>
      <div className="flex items-center gap-3">
        <TrackToggle
          source={Track.Source.Microphone}
          className="bg-bg2 hover:bg-bg3 text-fg1 border border-separator1 rounded-full p-2.5 transition-colors"
        />
        <button
          onClick={toggleAgentMute}
          className={`bg-bg2 hover:bg-bg3 text-fg1 border border-separator1 rounded-full p-2.5 transition-colors ${
            agentMuted ? "opacity-50" : ""
          }`}
          title={agentMuted ? "Unmute Agent" : "Mute Agent"}
        >
          {agentMuted ? (
            <VolumeX className="w-5 h-5" />
          ) : (
            <Volume2 className="w-5 h-5" />
          )}
        </button>
        <button
          onClick={() => window.location.reload()}
          className="bg-bgSerious1 hover:bg-fgSerious1 text-fgSerious1 hover:text-bg0 border border-fgSerious1 rounded-lg px-4 py-2 text-sm font-medium transition-colors"
        >
          Disconnect
        </button>
      </div>
    </div>
  );
}
