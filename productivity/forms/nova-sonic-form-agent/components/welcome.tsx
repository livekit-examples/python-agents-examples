import { CodeBlockIcon } from '@phosphor-icons/react/dist/ssr';
import { Button } from '@/components/ui/button';

interface WelcomeProps {
  disabled: boolean;
  startButtonText: string;
  onStartCall: () => void;
}

export const Welcome = ({
  disabled,
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeProps) => {
  return (
    <div
      ref={ref}
      inert={disabled}
      className="fixed inset-0 z-10 mx-auto flex h-svh flex-col items-center justify-center text-center"
    >
      <CodeBlockIcon size={64} className="mx-auto mb-4" />
      <h1 className="font-semibold">AWS Nova Sonic Form Assistant</h1>
      <p className="text-muted-foreground max-w-prose pt-1 font-medium">
        Start a call to complete your application with our AI-powered form assistant.
        <br />
        This demo uses AWS Nova Sonic for real-time voice interaction.
      </p>
      <Button variant="primary" size="lg" onClick={onStartCall} className="mt-12 w-64 font-mono">
        {startButtonText}
      </Button>
    </div>
  );
};
