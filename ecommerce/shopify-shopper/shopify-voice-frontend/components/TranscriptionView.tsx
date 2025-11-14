import useCombinedTranscriptions from "@/hooks/useCombinedTranscriptions";
import * as React from "react";

export default function TranscriptionView() {
  const combinedTranscriptions = useCombinedTranscriptions();
  const containerRef = React.useRef<HTMLDivElement>(null);

  // scroll to bottom when new transcription is added
  React.useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [combinedTranscriptions]);

  return (
    <div className="relative h-full w-full">
      {/* Fade-out gradient mask */}
      <div className="absolute top-0 left-0 right-0 h-6 pointer-events-none z-10" style={{ background: 'linear-gradient(to bottom, rgba(21, 9, 53, 0.1), transparent)' }} />
      <div className="absolute bottom-0 left-0 right-0 h-6 pointer-events-none z-10" style={{ background: 'linear-gradient(to top, rgba(21, 9, 53, 0.1), transparent)' }} />

      {/* Scrollable content */}
      <div ref={containerRef} className="h-full flex flex-col gap-2 overflow-y-auto px-3 py-6">
        {combinedTranscriptions.map((segment) => (
          <div
            id={segment.id}
            key={segment.id}
            className={
              segment.role === "assistant"
                ? "p-2 self-start rounded-md text-sm max-w-[85%]"
                : "p-2 self-end rounded-md text-sm max-w-[85%]"
            }
            style={{
              backgroundColor: segment.role === "assistant" ? 'rgba(219, 231, 237, 0.1)' : '#B941BA',
              color: segment.role === "assistant" ? '#DBE7ED' : '#DBE7ED',
              border: segment.role === "assistant" ? '1px solid rgba(219, 231, 237, 0.2)' : 'none'
            }}
          >
            {segment.text}
          </div>
        ))}
      </div>
    </div>
  );
}
