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
 * that is exactly what they would become if spoken. They are dimmed, italic and outlined
 * rather than filled, so the column reads as "not said yet" instead of a transcript of
 * things the caller already said. The italics are load-bearing: a dashed pill on its own
 * still reads as a button, and these are not clickable.
 */
export function SpeakHints({ hints }: SpeakHintsProps) {
  return (
    <div className="animate-in fade-in-0 slide-in-from-bottom-2 flex flex-col items-end gap-1.5 duration-300">
      <span className="text-fg3 text-xs">Try saying</span>
      {/* Opacity sits on this wrapper, not the pills: `fade-in-0` ends on opacity 1 and
          `animationFillMode: both` holds it there, so a class on the animated element
          would be overridden the moment the animation finished. */}
      <div className="flex flex-col items-end gap-1.5 opacity-70">
        {hints.map((hint, index) => (
          <p
            key={hint}
            className="border-separator1 text-fg3 animate-in fade-in-0 rounded-2xl border border-dashed px-4 py-2 text-sm italic leading-relaxed duration-300 lg:ml-12"
            style={{ animationDelay: `${index * 120}ms`, animationFillMode: 'both' }}
          >
            {hint}
          </p>
        ))}
      </div>
    </div>
  );
}
