import { BarVisualizer, useVoiceAssistant } from "@livekit/components-react";
import { Search } from "lucide-react";

export function EmptyState() {
  // Use useVoiceAssistant to get agent audio track
  const { state: agentState, audioTrack } = useVoiceAssistant();

  return (
    <div className="flex flex-col items-center justify-center py-20 px-6">
      <div className="flex flex-col items-center gap-6 max-w-md w-full">
        {/* Icon */}
        <div className="w-16 h-16 rounded-full bg-bgAccent1/20 border border-fgAccent1/30 flex items-center justify-center">
          <Search className="w-8 h-8 text-fgAccent1" />
        </div>

        {/* Audio Visualizer */}
        <div className="h-[150px] w-full max-w-xs bg-transparent">
          {audioTrack ? (
            <BarVisualizer
              state={agentState}
              barCount={5}
              trackRef={audioTrack}
              className="agent-visualizer"
              options={{ minHeight: 16 }}
            />
          ) : (
            <div className="agent-visualizer">
              <div className="flex items-center justify-center h-full text-fg3 text-sm">
                Waiting for agent...
              </div>
            </div>
          )}
        </div>

        {/* Text Content */}
        <div className="flex flex-col items-center gap-2 text-center">
          <h3 className="text-base font-semibold text-fg0">
            Ready to research
          </h3>
          <p className="text-sm text-fg3 leading-relaxed">
            Start a research job using voice commands
          </p>
        </div>
      </div>
    </div>
  );
}
