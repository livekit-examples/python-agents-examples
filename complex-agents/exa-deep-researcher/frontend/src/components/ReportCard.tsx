import { Streamdown } from "streamdown";
import { useEffect, useRef } from "react";

interface Report {
  reportTitle: string;
  reportContent: string;
}

interface ReportCardProps {
  report: Report;
}

/**
 * Converts plain URLs in the report content to clickable markdown links.
 * Also makes inline citation numbers clickable, linking to their sources.
 *
 * Handles multiple source formats:
 * 1. Inline citations: [1] -> clickable anchor link to #source-1
 * 2. Source with title: [1] Title: https://url.com -> [1] [Title](url)
 * 3. Source no title: [1]: https://url.com or [1] : https://url.com -> [1] [url](url)
 * 4. Source direct URL: [1] https://url.com -> [1] [url](url)
 */
function makeSourcesClickable(content: string): string {
  let processedContent = content;

  // First pass: Handle sources with empty/no title: [1]: https://url.com or [1] : https://url.com
  const sourceNoTitlePattern = /(\[\d+\])\s*:\s*(https?:\/\/[^\s]+)/g;
  processedContent = processedContent.replace(
    sourceNoTitlePattern,
    (match, number, url) => {
      const sourceNum = number.match(/\d+/)?.[0];
      return `<span id="source-${sourceNum}">${number}</span> [${url}](${url})`;
    }
  );

  // Second pass: Handle sources with title: [1] Title: https://url.com
  const sourceWithTitlePattern =
    /(\[\d+\])\s+([^:\n]+?):\s*(https?:\/\/[^\s]+)/g;
  processedContent = processedContent.replace(
    sourceWithTitlePattern,
    (match, number, title, url) => {
      const sourceNum = number.match(/\d+/)?.[0];
      const cleanTitle = title.trim();

      // If title is empty or just whitespace, use the URL
      if (!cleanTitle) {
        return `<span id="source-${sourceNum}">${number}</span> [${url}](${url})`;
      }

      return `<span id="source-${sourceNum}">${number}</span> [${cleanTitle}](${url})`;
    }
  );

  // Third pass: Handle direct URLs without colon: [1] https://url.com (that weren't caught above)
  const sourceDirectUrlPattern = /(\[\d+\])\s+(https?:\/\/[^\s<]+)/g;
  processedContent = processedContent.replace(
    sourceDirectUrlPattern,
    (match, number, url) => {
      // Skip if this was already processed (contains <span)
      if (match.includes("<span")) return match;

      const sourceNum = number.match(/\d+/)?.[0];
      return `<span id="source-${sourceNum}">${number}</span> [${url}](${url})`;
    }
  );

  // Make inline citations clickable (but not in the Sources section)
  const sourcesIndex = processedContent.indexOf("\nSources\n");

  if (sourcesIndex !== -1) {
    const mainContent = processedContent.substring(0, sourcesIndex);
    const sourcesSection = processedContent.substring(sourcesIndex);

    // Pattern to match inline citations like [1], [2], etc.
    const inlineCitationPattern = /(?<!^|\n)(\[\d+\])(?!\s*[^\n]*https?:\/\/)/g;

    const processedMain = mainContent.replace(
      inlineCitationPattern,
      (match) => {
        const sourceNum = match.match(/\d+/)?.[0];
        return `[${match}](#source-${sourceNum})`;
      }
    );

    processedContent = processedMain + sourcesSection;
  }

  return processedContent;
}

export function ReportCard({ report }: ReportCardProps) {
  const contentRef = useRef<HTMLDivElement>(null);

  // Process the report content to make sources clickable
  const processedContent = makeSourcesClickable(report.reportContent);

  // Add target="_blank" and rel="noopener noreferrer" to all links for security
  useEffect(() => {
    if (contentRef.current) {
      const links = contentRef.current.querySelectorAll("a");
      links.forEach((link) => {
        link.setAttribute("target", "_blank");
        link.setAttribute("rel", "noopener noreferrer");
      });
    }
  }, [processedContent]);

  return (
    <div
      data-slot="report-card"
      className="bg-bgSuccess1/30 border border-separatorSuccess rounded-xl p-6 shadow-sm"
    >
      <div className="flex items-center gap-2 mb-4">
        <h2 className="font-bold text-fg0 text-base">{report.reportTitle}</h2>
      </div>

      <div>
        {report.reportContent ? (
          <div className="bg-bg0 border border-separator1 rounded-lg p-6 max-h-[800px] overflow-y-auto">
            <div
              ref={contentRef}
              className="text-sm text-fg1 leading-relaxed prose prose-invert max-w-none 
                [&_a]:text-fgAccent1 [&_a]:underline [&_a]:decoration-fgAccent1/30 
                [&_a:hover]:decoration-fgAccent1 [&_a]:transition-colors 
                [&_a]:cursor-pointer [&_a]:wrap-break-word"
              style={{ whiteSpace: "pre-wrap", wordWrap: "break-word" }}
            >
              <Streamdown>{processedContent}</Streamdown>
            </div>
          </div>
        ) : (
          <div className="bg-bg1 border border-separator1 rounded-lg p-4 text-center">
            <p className="text-sm text-fg3">
              Report content not available. Check console for details.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
