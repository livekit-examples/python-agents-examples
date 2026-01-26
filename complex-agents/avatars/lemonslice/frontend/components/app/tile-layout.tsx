import React, { useMemo } from 'react';
import { Track } from 'livekit-client';
import { AnimatePresence, motion } from 'motion/react';
import {
  type TrackReference,
  VideoTrack,
  useLocalParticipant,
  useTracks,
  useVoiceAssistant,
} from '@livekit/components-react';
import { AgentAudioVisualizerBar } from '@/components/agents-ui/agent-audio-visualizer-bar';
import { cn } from '@/lib/shadcn/utils';

const MotionContainer = motion.create('div');

const ANIMATION_TRANSITION = {
  type: 'spring',
  stiffness: 675,
  damping: 75,
  mass: 1,
};

const VIDEO_DIMENSIONS = {
  width: 400,
  height: 533,
};

export function useLocalTrackRef(source: Track.Source) {
  const { localParticipant } = useLocalParticipant();
  const publication = localParticipant.getTrackPublication(source);
  const trackRef = useMemo<TrackReference | undefined>(
    () => (publication ? { source, participant: localParticipant, publication } : undefined),
    [source, publication, localParticipant]
  );
  return trackRef;
}

interface TileLayoutProps {
  chatOpen: boolean;
  mode?: 'roleplay' | 'coaching';
  children?: React.ReactNode;
}

export function TileLayout({ mode, children }: TileLayoutProps) {
  const {
    state: agentState,
    audioTrack: agentAudioTrack,
    videoTrack: agentVideoTrack,
  } = useVoiceAssistant();
  const [screenShareTrack] = useTracks([Track.Source.ScreenShare]);
  const cameraTrack: TrackReference | undefined = useLocalTrackRef(Track.Source.Camera);

  const isCameraEnabled = cameraTrack && !cameraTrack.publication.isMuted;
  const isScreenShareEnabled = screenShareTrack && !screenShareTrack.publication.isMuted;

  const isAvatar = agentVideoTrack !== undefined;
  const videoWidth = agentVideoTrack?.publication.dimensions?.width ?? 0;
  const videoHeight = agentVideoTrack?.publication.dimensions?.height ?? 0;

  // Determine border color based on mode
  const getBorderColor = () => {
    if (!mode) return 'border-transparent';
    if (mode === 'coaching') return 'border-green-500';
    return 'border-blue-500';
  };

  // Get background color based on mode
  const getBackgroundColor = () => {
    if (!mode) return '';
    if (mode === 'coaching') return 'bg-green-500/5';
    return 'bg-blue-500/5';
  };

  // Get mode label
  const getModeLabel = () => {
    if (!mode) return '';
    return mode === 'coaching' ? 'Coaching' : 'Roleplay';
  };

  return (
    <div className="pointer-events-none fixed inset-x-0 top-8 bottom-32 z-50 md:top-12 md:bottom-40">
      <div className="relative mx-auto h-full px-4 md:px-8">
        <div className="flex h-full items-start justify-center pt-8 md:pt-12">
          <div className="flex flex-col items-center gap-4 max-h-full">
            <div
              className={cn(
                'border-border/50 rounded-3xl border p-6 transition-colors duration-500',
                'max-h-[calc(100%-5rem)]',
                getBackgroundColor()
              )}
            >
              <div className="flex items-center justify-center gap-4">
                {/* Agent Video */}
                <AnimatePresence mode="popLayout">
                  {!isAvatar && (
                    // Audio Agent
                    <MotionContainer
                      key="agent"
                      layoutId="agent"
                      initial={{
                        opacity: 0,
                        scale: 0,
                      }}
                      animate={{
                        opacity: 1,
                        scale: 1,
                      }}
                      transition={ANIMATION_TRANSITION}
                      className={cn(
                        'bg-background rounded-lg border-4 drop-shadow-xl transition-colors',
                        'h-[min(400px,calc(100vh-20rem))] md:h-[min(480px,calc(100vh-24rem))] w-auto aspect-[3/4]',
                        getBorderColor()
                      )}
                    >
                      <AgentAudioVisualizerBar
                        barCount={5}
                        state={agentState}
                        audioTrack={agentAudioTrack}
                        className={cn('flex h-full items-center justify-center gap-1 px-4 py-2')}
                      >
                        <span
                          className={cn([
                            'bg-muted min-h-2.5 w-2.5 rounded-full',
                            'origin-center transition-colors duration-250 ease-linear',
                            'data-[lk-highlighted=true]:bg-foreground data-[lk-muted=true]:bg-muted',
                          ])}
                        />
                      </AgentAudioVisualizerBar>
                    </MotionContainer>
                  )}

                  {isAvatar && (
                    // Avatar Agent
                    <MotionContainer
                      key="avatar"
                      layoutId="avatar"
                      initial={{
                        scale: 1,
                        opacity: 1,
                        maskImage:
                          'radial-gradient(circle, rgba(0, 0, 0, 1) 0, rgba(0, 0, 0, 1) 20px, transparent 20px)',
                        filter: 'blur(20px)',
                      }}
                      animate={{
                        maskImage:
                          'radial-gradient(circle, rgba(0, 0, 0, 1) 0, rgba(0, 0, 0, 1) 500px, transparent 500px)',
                        filter: 'blur(0px)',
                        borderRadius: 12,
                      }}
                      transition={{
                        ...ANIMATION_TRANSITION,
                        maskImage: {
                          duration: 1,
                        },
                        filter: {
                          duration: 1,
                        },
                      }}
                      className={cn(
                        'overflow-hidden border-4 bg-black drop-shadow-xl transition-colors',
                        'h-[min(400px,calc(100vh-20rem))] md:h-[min(480px,calc(100vh-24rem))] w-auto aspect-[3/4]',
                        getBorderColor()
                      )}
                    >
                      <VideoTrack
                        width={videoWidth}
                        height={videoHeight}
                        trackRef={agentVideoTrack}
                        className="h-full w-full object-cover"
                      />
                    </MotionContainer>
                  )}
                </AnimatePresence>

                {/* User Camera */}
                <AnimatePresence>
                  {((cameraTrack && isCameraEnabled) ||
                    (screenShareTrack && isScreenShareEnabled)) && (
                    <MotionContainer
                      key="camera"
                      layout="position"
                      layoutId="camera"
                      initial={{
                        opacity: 0,
                        scale: 0,
                      }}
                      animate={{
                        opacity: 1,
                        scale: 1,
                      }}
                      exit={{
                        opacity: 0,
                        scale: 0,
                      }}
                      transition={ANIMATION_TRANSITION}
                      className={cn(
                        'bg-muted overflow-hidden rounded-lg border-4 drop-shadow-xl transition-colors',
                        'h-[min(400px,calc(100vh-20rem))] md:h-[min(480px,calc(100vh-24rem))] w-auto aspect-[3/4]',
                        getBorderColor()
                      )}
                    >
                      <VideoTrack
                        trackRef={cameraTrack || screenShareTrack}
                        width={
                          (cameraTrack || screenShareTrack)?.publication.dimensions?.width ?? 0
                        }
                        height={
                          (cameraTrack || screenShareTrack)?.publication.dimensions?.height ?? 0
                        }
                        className="h-full w-full object-cover"
                      />
                    </MotionContainer>
                  )}
                </AnimatePresence>
              </div>

              {/* Mode indicator text */}
              {mode && (
                <div className="text-muted-foreground mt-4 text-center text-sm font-medium">
                  {getModeLabel()}
                </div>
              )}
            </div>

            {/* Timer and button controls */}
            {children && (
              <div className="pointer-events-auto flex w-full max-w-[850px] items-center justify-between gap-4 px-2">
                {children}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
