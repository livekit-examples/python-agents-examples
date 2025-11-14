import { TrackToggle, useLocalParticipant } from "@livekit/components-react";
import { Track } from "livekit-client";
import { MultibandAudioVisualizer } from "@/components/visualization/multiband";
import { DeviceSelector } from "@/components/device-selector";
import { useEffect, useState } from "react";
import { Mic, MicOff } from "lucide-react";

type MicrophoneButtonProps = {
  localMultibandVolume: Float32Array[];
  isSpaceBarEnabled?: boolean;
};
export const MicrophoneButton = ({
  localMultibandVolume,
  isSpaceBarEnabled = false,
}: MicrophoneButtonProps) => {
  const { localParticipant } = useLocalParticipant();
  const [isMuted, setIsMuted] = useState(localParticipant.isMicrophoneEnabled);
  const [isSpaceBarPressed, setIsSpaceBarPressed] = useState(false);

  useEffect(() => {
    setIsMuted(localParticipant.isMicrophoneEnabled === false);
  }, [localParticipant.isMicrophoneEnabled]);

  useEffect(() => {
    if (!isSpaceBarEnabled) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.code === "Space") {
        localParticipant.setMicrophoneEnabled(true);
        setIsSpaceBarPressed(true);
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === "Space") {
        localParticipant.setMicrophoneEnabled(false);
        setIsSpaceBarPressed(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [isSpaceBarEnabled, localParticipant]);

  return (
    <div
      className={`flex items-center justify-center gap-2 px-2 py-[6px] bg-transparent rounded text-white border border-white/20 hover:bg-white/10 active:translate-y-[2px] active:scale-[0.99] transition-all ease-out duration-250 ${
        isSpaceBarPressed ? "scale-90 border-white/20-text border" : "scale-100"
      }`}
    >
      <TrackToggle
        source={Track.Source.Microphone}
        className={
          "flex items-center justify-center gap-2 h-full " +
          (isMuted ? "opacity-50" : "")
        }
        showIcon={false}
      >
        {isMuted ? (
          <MicOff className="w-4 h-4 text-white" />
        ) : (
          <Mic className="w-4 h-4 text-white" />
        )}
        <MultibandAudioVisualizer
          state="speaking"
          barWidth={2}
          minBarHeight={2}
          maxBarHeight={16}
          accentColor={"white"}
          accentShade={950}
          frequencies={localMultibandVolume}
          borderRadius={5}
          gap={2}
        />
      </TrackToggle>
      <DeviceSelector kind="audioinput" />
    </div>
  );
};
