import { useState } from "react";

interface ResearchNote {
  subtopic: string;
  summaryMarkdown: string;
  citations: Array<{
    id: string;
    url: string;
    title: string;
    quote: string;
  }>;
  ts: number;
}

interface ResearchNotesListProps {
  notes: ResearchNote[];
}

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

export function ResearchNotesList({ notes }: ResearchNotesListProps) {
  const [expandedNotes, setExpandedNotes] = useState<Set<string>>(new Set());

  if (notes.length === 0) return null;

  const toggleExpanded = (noteKey: string) => {
    setExpandedNotes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(noteKey)) {
        newSet.delete(noteKey);
      } else {
        newSet.add(noteKey);
      }
      return newSet;
    });
  };

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-fg0">Research Findings</h2>
        <div className="text-xs text-fg3">
          {notes.length} {notes.length === 1 ? "finding" : "findings"}
        </div>
      </div>
      <div className="bg-bg1 border border-separator1 rounded-lg divide-y divide-separator1">
        {notes
          .filter((note) => {
            const title = note.subtopic?.toLowerCase().trim() || "";
            return (
              title && title !== "untitled" && !title.startsWith("untitled")
            );
          })
          .map((note, idx) => {
            const noteKey = `${note.subtopic}-${note.ts}-${idx}`;
            const isExpanded = expandedNotes.has(noteKey);
            const validCitations = note.citations.filter((c) => {
              const title = c.title?.toLowerCase().trim() || "";
              return (
                title && title !== "untitled" && !title.startsWith("untitled")
              );
            });

            const citationsToShow = isExpanded
              ? validCitations
              : validCitations.slice(0, 3);

            return (
              <div
                key={noteKey}
                data-slot="research-note"
                className="px-3 py-2 hover:bg-bg2 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3
                        className="font-medium text-fg0 text-xs flex-1 truncate"
                        title={note.subtopic}
                      >
                        {note.subtopic}
                      </h3>
                      <time
                        className="text-[10px] text-fg4 whitespace-nowrap shrink-0"
                        dateTime={new Date(note.ts * 1000).toISOString()}
                      >
                        {new Date(note.ts * 1000).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </time>
                    </div>
                    <div
                      className="text-[10px] text-fg2 line-clamp-1 mb-1"
                      dangerouslySetInnerHTML={{
                        __html: note.summaryMarkdown
                          .replace(/\n/g, " ")
                          .substring(0, 150),
                      }}
                    />
                    {validCitations.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {citationsToShow.map((cit) => (
                          <a
                            key={cit.id}
                            href={cit.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center text-[9px] text-fgAccent1 hover:text-fgAccent2 bg-bg2 border border-separator1 hover:border-fgAccent1 rounded px-2 py-0.5 transition-colors truncate max-w-[200px]"
                            title={cit.title}
                          >
                            {truncate(cit.title, 30)}
                          </a>
                        ))}
                        {validCitations.length > 3 && (
                          <button
                            onClick={() => toggleExpanded(noteKey)}
                            className="inline-flex items-center text-[9px] text-fg4 hover:text-fgAccent1 bg-bg2 border border-separator1 hover:border-fgAccent1 rounded px-2 py-0.5 transition-colors cursor-pointer"
                            title={
                              isExpanded
                                ? "Show less sources"
                                : `Show ${validCitations.length - 3} more sources`
                            }
                          >
                            {isExpanded
                              ? "−"
                              : `+${validCitations.length - 3}`}
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
      </div>
    </div>
  );
}
