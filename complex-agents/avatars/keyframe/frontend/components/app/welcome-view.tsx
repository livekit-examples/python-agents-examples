import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref}>
      <section className="bg-background flex flex-col items-center justify-center text-center">
        <p className="text-foreground max-w-prose pt-1 text-lg leading-7 font-medium">
          Keyframe Labs avatar demo
        </p>
        <p className="text-muted-foreground max-w-md pt-2 text-sm leading-5">
          Talk with two personas in one live demo. Start with Cosmo for expressive conversation,
          then switch to Lyra for an airline support scenario.
        </p>

        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-6 w-64 rounded-full font-mono text-xs font-bold tracking-wider uppercase"
        >
          {startButtonText}
        </Button>
      </section>

      <div className="fixed bottom-5 left-0 flex w-full items-center justify-center gap-1">
        <p className="text-muted-foreground max-w-prose pt-1 text-xs leading-5 font-normal text-pretty md:text-sm">
          Powered by{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://keyframelabs.com"
            className="underline"
          >
            Keyframe Labs
          </a>{' '}
          &{' '}
          <a
            target="_blank"
            rel="noopener noreferrer"
            href="https://livekit.io"
            className="underline"
          >
            LiveKit
          </a>
        </p>
      </div>
    </div>
  );
};
