'use client';

import React from 'react';
import { Track } from 'livekit-client';
import { useRoomContext, useTrackToggle } from '@livekit/components-react';
import {
  MicrophoneIcon,
  MicrophoneSlashIcon,
  PhoneDisconnectIcon,
} from '@phosphor-icons/react/dist/ssr';
import { Button } from '@/components/ui/button';

export const SimpleControlBar = () => {
  const { buttonProps: micButtonProps, enabled: micEnabled } = useTrackToggle({
    source: Track.Source.Microphone,
  });
  const room = useRoomContext();

  return (
    <div className="flex items-center justify-center gap-4">
      {/* Mic toggle button */}
      <Button
        {...micButtonProps}
        size="lg"
        className={`rounded-full p-4 ${
          micEnabled
            ? 'border border-gray-300 bg-gray-200 text-gray-800 hover:bg-gray-300'
            : 'bg-red-500 text-white hover:bg-red-600'
        }`}
      >
        {micEnabled ? <MicrophoneIcon size={24} /> : <MicrophoneSlashIcon size={24} />}
      </Button>

      {/* Leave call button */}
      <Button
        onClick={() => room.disconnect()}
        size="lg"
        className="flex items-center gap-2 rounded-full bg-red-500 px-6 py-4 text-white hover:bg-red-600"
      >
        <PhoneDisconnectIcon size={24} />
        <span>Leave Call</span>
      </Button>
    </div>
  );
};
