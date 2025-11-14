"use client";

import { CloseIcon } from "@/components/CloseIcon";
import { NoAgentNotification } from "@/components/NoAgentNotification";
import TranscriptionView from "@/components/TranscriptionView";
import {
  BarVisualizer,
  DisconnectButton,
  RoomAudioRenderer,
  RoomContext,
  VideoTrack,
  VoiceAssistantControlBar,
  useVoiceAssistant,
} from "@livekit/components-react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Room,
  RoomEvent,
  RemoteParticipant,
  LocalParticipant,
  RpcInvocationData
} from "livekit-client";
import { useCallback, useEffect, useState } from "react";
import type { ConnectionDetails } from "./api/connection-details/route";

export default function Page() {
  const [room] = useState(new Room());

  const onConnectButtonClicked = useCallback(async () => {
    // Generate room connection details, including:
    //   - A random Room name
    //   - A random Participant name
    //   - An Access Token to permit the participant to join the room
    //   - The URL of the LiveKit server to connect to
    //
    // In real-world application, you would likely allow the user to specify their
    // own participant name, and possibly to choose from existing rooms to join.

    const url = new URL(
      process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT ?? "/api/connection-details",
      window.location.origin
    );
    const response = await fetch(url.toString());
    const connectionDetailsData: ConnectionDetails = await response.json();

    await room.connect(connectionDetailsData.serverUrl, connectionDetailsData.participantToken);
    await room.localParticipant.setMicrophoneEnabled(true);
  }, [room]);

  useEffect(() => {
    room.on(RoomEvent.MediaDevicesError, onDeviceFailure);

    // RPC Handler for Navigation
    if (room && room.localParticipant) {
      const handleNavigateRpc = async (rpcInvocation: RpcInvocationData): Promise<string> => {
        let responseMessage: string;
        try {
          // rpcInvocation.payload is a string when sent with json.dumps from Python agent
          const payload = JSON.parse(rpcInvocation.payload);
          console.log("Received and parsed client.navigate RPC data:", payload);

          if (payload && payload.url) {
            const navigationData = {
              type: 'navigateFromNextJs', // Message type for popup.js
              url: payload.url,
            };
            console.log("Sending navigation message to extension:", navigationData);
            // IMPORTANT: Update 'http://localhost:3000' if your Next.js app is served from a different origin.
            // This should match the origin check in your extension's popup.js.
            window.parent.postMessage(navigationData, '*');
            responseMessage = "Success: Navigation message sent to extension.";
          } else {
            console.error("Invalid navigation RPC data: URL missing", payload);
            responseMessage = "Error: Invalid navigation RPC data format - URL missing.";
          }
        } catch (error) {
          console.error("Error processing navigation RPC:", error);
          responseMessage = "Error: " + (error instanceof Error ? error.message : String(error));
        }
        return responseMessage;
      };

      console.log("Registering RPC method: client.navigate");
      room.localParticipant.registerRpcMethod("client.navigate", handleNavigateRpc);

      // Cleanup function to unregister the RPC method
      return () => {
        if (room && room.localParticipant) {
          console.log("Unregistering RPC method: client.navigate");
          room.localParticipant.unregisterRpcMethod("client.navigate");
        }
        room.off(RoomEvent.MediaDevicesError, onDeviceFailure); // Also move the original off here
      };
    } else {
      // Only unregister MediaDevicesError if the RPC part wasn't set up
      return () => {
        room.off(RoomEvent.MediaDevicesError, onDeviceFailure);
      };
    }
  }, [room]); // room is the main dependency

  return (
    <main
      className="h-screen w-full flex flex-col"
      style={{
        background: 'linear-gradient(180deg, #150935 0%, rgba(90, 45, 140, 0.8) 40%, rgba(90, 45, 140, 0.6) 55%, rgba(185, 65, 186, 0.3) 70%, rgba(194, 67, 188, 0.4) 80%, rgba(194, 67, 188, 0.8) 90%, #C243BC 100%)',
        backgroundColor: '#150935',
        '--lk-bg': 'transparent',
        '--lk-bg-2': 'transparent'
      } as React.CSSProperties}
    >
      <style jsx>{`
        /* LiveKit audio visualizer styling is now handled in globals.css */
      `}</style>
      <RoomContext.Provider value={room}>
        <div className="lk-room-container w-full h-full flex flex-col px-2 py-2" style={{ background: 'transparent' }}>
          <SimpleVoiceAssistant onConnectButtonClicked={onConnectButtonClicked} />
        </div>
      </RoomContext.Provider>
    </main>
  );
}

function SimpleVoiceAssistant(props: { onConnectButtonClicked: () => void }) {
  const { state: agentState } = useVoiceAssistant();

  return (
    <div className="h-full flex flex-col">
      <AnimatePresence mode="wait">
        {agentState === "disconnected" ? (
          <motion.div
            key="disconnected"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3, ease: [0.09, 1.04, 0.245, 1.055] }}
            className="flex items-center justify-center h-full px-2"
          >
            <motion.button
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.3, delay: 0.1 }}
              className="uppercase px-3 py-2 rounded-md text-sm w-full max-w-[200px] font-medium"
              style={{ backgroundColor: '#B941BA', color: '#DBE7ED' }}
              onClick={() => props.onConnectButtonClicked()}
            >
              Start conversation
            </motion.button>
          </motion.div>
        ) : (
          <motion.div
            key="connected"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3, ease: [0.09, 1.04, 0.245, 1.055] }}
            className="flex flex-col h-full gap-2"
          >
            <div className="shrink-0">
              <AgentVisualizer />
            </div>
            <div className="flex-1 min-h-0 flex flex-col">
              <TranscriptionView />
            </div>
            <div className="shrink-0">
              <ControlBar onConnectButtonClicked={props.onConnectButtonClicked} />
            </div>
            <RoomAudioRenderer />
            <NoAgentNotification state={agentState} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function AgentVisualizer() {
  const { state: agentState, videoTrack, audioTrack } = useVoiceAssistant();

  if (videoTrack) {
    return (
      <div className="aspect-square w-full max-w-[280px] mx-auto rounded-lg overflow-hidden">
        <VideoTrack trackRef={videoTrack} />
      </div>
    );
  }
  return (
    <div className="h-[150px] w-full pt-4">
      <BarVisualizer
        state={agentState}
        barCount={5}
        trackRef={audioTrack}
        className="agent-visualizer"
        options={{ minHeight: 16 }}
      />
    </div>
  );
}

function ControlBar(props: { onConnectButtonClicked: () => void }) {
  const { state: agentState } = useVoiceAssistant();

  return (
    <div className="relative h-[50px]">
      <AnimatePresence>
        {agentState === "disconnected" && (
          <motion.button
            initial={{ opacity: 0, top: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, top: "-10px" }}
            transition={{ duration: 1, ease: [0.09, 1.04, 0.245, 1.055] }}
            className="uppercase absolute left-1/2 -translate-x-1/2 px-3 py-2 rounded-md text-sm font-medium"
            style={{ backgroundColor: '#B941BA', color: '#DBE7ED' }}
            onClick={() => props.onConnectButtonClicked()}
          >
            Start conversation
          </motion.button>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {agentState !== "disconnected" && agentState !== "connecting" && (
          <motion.div
            initial={{ opacity: 0, top: "10px" }}
            animate={{ opacity: 1, top: 0 }}
            exit={{ opacity: 0, top: "-10px" }}
            transition={{ duration: 0.4, ease: [0.09, 1.04, 0.245, 1.055] }}
            className="flex h-8 absolute left-1/2 -translate-x-1/2 justify-center items-center gap-2 px-3 rounded-md"
            style={{ backgroundColor: '#DBE7ED' }}
          >
            <VoiceAssistantControlBar controls={{ leave: false }} />
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <DisconnectButton
                style={{
                  background: 'transparent',
                  border: 'none',
                  padding: '2px',
                  color: '#150935',
                  opacity: 1
                }}
              >
                <CloseIcon />
              </DisconnectButton>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function onDeviceFailure(error: Error) {
  console.error(error);
  alert(
    "Error acquiring camera or microphone permissions. Please make sure you grant the necessary permissions in your browser and reload the tab"
  );
}
