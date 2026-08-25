interface SpeakHintsProps {
  hints: string[];
}

/**
 * Openers the caller can say, offered once the agent has greeted them.
 *
 * Deliberately not buttons. A click would send the text straight to the agent and skip the
 * microphone, which is the one part of this demo worth showing; the hints exist to get
 * someone talking, not to give them a way around it.
 *
 * Shaped like the caller's own messages -- right-aligned, same pill, same type -- because
 * that is exactly what they would become if spoken. They are dimmed and outlined rather
 * than filled, so the column reads as "not said yet" instead of a transcript of things the
 * caller already said.
 */
export function SpeakHints({ hints }: SpeakHintsProps) {
  return (
    <div className="animate-in fade-in-0 slide-in-from-bottom-2 flex flex-col items-end gap-1.5 duration-300">
      <span className="text-fg3 text-xs">Try saying</span>
      {hints.map((hint, index) => (
        <p
          key={hint}
          className="border-separator1 text-fg3 animate-in fade-in-0 rounded-2xl border border-dashed px-4 py-2 text-sm leading-relaxed duration-300 lg:ml-12"
          style={{ animationDelay: `${index * 120}ms`, animationFillMode: 'both' }}
        >
          {hint}
        </p>
      ))}
    </div>
  );
}
