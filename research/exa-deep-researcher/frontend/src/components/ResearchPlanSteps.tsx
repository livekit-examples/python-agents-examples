import { HelpCircle, FileText, Search, Package, CheckCircle2, Loader2 } from "lucide-react";

interface PlanStep {
  id: string;
  label: string;
  icon: string;
  status: "pending" | "active" | "completed";
  description?: string;
  timestamp?: number;
}

interface ResearchPlanStepsProps {
  steps: PlanStep[];
  title?: string | null;
}

// Map icon names to Lucide React components
const iconMap: Record<string, typeof HelpCircle> = {
  clarification: HelpCircle,
  planning: FileText,
  topic: Search,
  organizing: Package,
  report: FileText,
};

function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3) + "...";
}

export function ResearchPlanSteps({ steps, title }: ResearchPlanStepsProps) {
  if (steps.length === 0) return null;

  return (
    <div className="px-4 pt-4 pb-3">
      <div className="bg-bg1 border border-separator1 rounded-xl px-4 pt-4 pb-3 shadow-sm overflow-visible">
        <div className="flex flex-col items-center gap-3 overflow-visible">
          {title && (
            <h3 className="text-xs font-semibold text-fg0">{title}</h3>
          )}
          <div className="flex flex-row items-center gap-2 justify-center w-full overflow-x-auto overflow-y-visible pt-1 pb-1 scrollbar-thin scrollbar-thumb-separator1 scrollbar-track-transparent">
            {steps.map((step, idx) => {
              const isLast = idx === steps.length - 1;
              const isActive = step.status === "active";
              const isCompleted = step.status === "completed";
              const prevStep = idx > 0 ? steps[idx - 1] : null;
              const prevCompleted = prevStep?.status === "completed";

              const IconComponent = iconMap[step.icon] || FileText;

              return (
                <div key={step.id} className="flex items-center gap-2 shrink-0 overflow-visible">
                  <div className="flex flex-col items-center gap-2 min-w-[96px] max-w-[96px] overflow-visible">
                    {/* Icon container */}
                    <div className="relative overflow-visible z-10">
                      <div
                        className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center border transition-all relative z-0 ${
                          isActive
                            ? "bg-bgAccent1/20 border-fgAccent1 text-fgAccent1"
                            : isCompleted
                            ? "bg-bg2 border-separator1 text-fg2"
                            : "bg-bg2 border-separator1 text-fg4"
                        }`}
                      >
                        {isActive ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <IconComponent className="w-4 h-4" />
                        )}
                      </div>
                      {/* Active indicator (small pulse dot) */}
                      {isActive && (
                        <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-fgAccent1 rounded-full animate-pulse border border-bg0 z-20" />
                      )}
                      {/* Completed checkmark */}
                      {isCompleted && (
                        <div className="absolute -top-0.5 -right-0.5 w-3 h-3 bg-fgAccent1/30 border border-fgAccent1/50 rounded-full flex items-center justify-center z-50">
                          <CheckCircle2 className="w-2 h-2 text-fgAccent1" />
                        </div>
                      )}
                    </div>

                    {/* Text container with fixed height */}
                    <div className="flex flex-col items-center gap-0.5 w-full min-h-[40px] justify-center">
                      <h4
                        className={`text-[10px] font-semibold text-center leading-tight line-clamp-2 ${
                          isActive
                            ? "text-fgAccent1"
                            : isCompleted
                            ? "text-fg2"
                            : "text-fg3"
                        }`}
                        title={step.label}
                      >
                        {truncate(step.label, 35)}
                      </h4>
                      {step.description && (
                        <p className="text-[8px] text-fg4 text-center line-clamp-1">
                          {step.description}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Connector */}
                  {!isLast && (
                    <div
                      className={`h-0.5 w-8 min-w-[32px] transition-colors ${
                        prevCompleted
                          ? "bg-fgAccent1/30"
                          : isActive
                          ? "bg-fgAccent1/20"
                          : "bg-separator1"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
