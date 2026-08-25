import { Badge } from '@/components/bytes';

interface SpeakHintsProps {
  hints: string[];
}

/**
 * Openers the caller can say, offered once the agent has greeted them.
 *
 * Deliberately not buttons. A click would send the text straight to the agent and skip the
 * microphone, which is the one part of this demo worth showing; the hints exist to get
 * someone talking, not to give them a way around it.
 */
export function SpeakHints({ hints }: SpeakHintsProps) {
  return (
    <div className="animate-in fade-in-0 slide-in-from-bottom-2 flex flex-wrap items-center justify-end gap-2 pl-14 duration-300">
      <span className="text-fg3 text-xs">Try saying</span>
      {hints.map((hint, index) => (
        <span
          key={hint}
          className="animate-in fade-in-0 inline-flex duration-300"
          style={{ animationDelay: `${index * 120}ms`, animationFillMode: 'both' }}
        >
          <Badge variant="muted" size="large">
            {hint}
          </Badge>
        </span>
      ))}
    </div>
  );
}
