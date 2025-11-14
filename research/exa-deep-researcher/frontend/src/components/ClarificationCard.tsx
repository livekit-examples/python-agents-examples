import { HelpCircle } from "lucide-react";

interface Clarification {
  question: string;
  originalQuery: string;
}

interface ClarificationCardProps {
  clarification: Clarification;
}

export function ClarificationCard({ clarification }: ClarificationCardProps) {
  return (
    <div className="p-6 pb-4">
      <div className="bg-bgAccent1/20 border border-separatorAccent rounded-xl p-6 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="shrink-0">
            <HelpCircle className="w-6 h-6 text-fgAccent1" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="text-sm font-semibold text-fgAccent1">
                Clarification Needed
              </h3>
            </div>
            <p className="text-sm text-fg0 mb-2 leading-relaxed">
              {clarification.question}
            </p>
            <div className="text-xs text-fg3 mt-3 pt-3 border-t border-separator1">
              Original query:{" "}
              <span className="font-medium text-fg2">
                {clarification.originalQuery}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

