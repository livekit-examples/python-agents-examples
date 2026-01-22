'use client';

import { useState } from 'react';
import { useChat } from '@livekit/components-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';

interface CoachingButtonProps {
  disabled?: boolean;
  className?: string;
}

export function CoachingButton({ disabled = false, className }: CoachingButtonProps) {
  const { send } = useChat();
  const [isSending, setIsSending] = useState(false);

  const handleClick = async () => {
    try {
      setIsSending(true);
      // Send a message that triggers the coaching mode
      await send('How am I doing?');
    } catch (error) {
      console.error('Failed to request coaching:', error);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <Button
      size="lg"
      variant="outline"
      onClick={handleClick}
      disabled={disabled || isSending}
      className={cn(
        'border-green-500/30 bg-green-500/10 text-green-500 hover:border-green-500/50 hover:bg-green-500/20',
        'font-semibold tracking-wide',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className
      )}
    >
      {isSending ? (
        <>
          <svg
            className="mr-2 -ml-1 h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          Asking coach...
        </>
      ) : (
        <>
          <svg
            className="mr-2 h-4 w-4"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          How am I doing?
        </>
      )}
    </Button>
  );
}
