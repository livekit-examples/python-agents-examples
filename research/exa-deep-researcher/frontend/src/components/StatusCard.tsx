import { FileText, Search, Package, HelpCircle } from "lucide-react";

interface StatusCardProps {
  phase: string;
  title: string;
  message: string;
  progressPct?: number;
  stats: Record<string, unknown>;
  phaseConfig: {
    label: string;
    icon: string;
    bg: string;
    border: string;
    text: string;
    progressBg: string;
    dot: string;
  };
}

const iconMap: Record<string, typeof FileText> = {
  "file-text": FileText,
  "search": Search,
  "package": Package,
  "help-circle": HelpCircle,
};

export function StatusCard({
  phase,
  title,
  message,
  progressPct,
  stats,
  phaseConfig,
}: StatusCardProps) {
  const IconComponent = iconMap[phaseConfig.icon] || FileText;

  return (
    <div
      data-slot="status-card"
      className={`lg:col-span-2 bg-bg1 ${phaseConfig.border} border rounded-xl shadow-sm overflow-hidden`}
    >
      <div
        className={`${phaseConfig.bg} border-b ${phaseConfig.border} px-4 py-3`}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div
              className={`${phaseConfig.dot} w-2 h-2 rounded-full animate-pulse`}
            />
            <div className="flex items-center gap-2">
              <IconComponent className={`w-4 h-4 ${phaseConfig.text}`} />
              <span
                className={`text-xs font-semibold ${phaseConfig.text}`}
              >
                {phaseConfig.label}
              </span>
            </div>
          </div>
          {progressPct !== undefined && (
            <div
              className={`text-sm font-bold ${phaseConfig.text} whitespace-nowrap`}
            >
              {Math.round(progressPct)}%
            </div>
          )}
        </div>
      </div>

      <div className="p-4 flex flex-col gap-3">
        <div>
          <h3
            className="font-semibold text-fg0 text-sm mb-1.5 line-clamp-2"
            title={title}
          >
            {title}
          </h3>
          <p
            className={`text-xs ${phaseConfig.text} opacity-80 leading-relaxed line-clamp-2`}
            title={message}
          >
            {message}
          </p>
        </div>

        {progressPct !== undefined && (
          <div className="space-y-1">
            <div className="w-full bg-bg2 rounded-full h-2 overflow-hidden">
              <div
                className={`h-full ${phaseConfig.progressBg} transition-all duration-500 ease-out rounded-full`}
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        )}

        {Object.keys(stats).length > 0 && (
          <div className="border-t border-separator1 pt-3 mt-1">
            <div className="flex flex-wrap gap-x-4 gap-y-2">
              {Object.entries(stats)
                .slice(0, 4)
                .map(([key, value]) => (
                  <div key={key} className="flex items-baseline gap-1.5">
                    <span className="text-sm font-bold text-fg0">
                      {String(value)}
                    </span>
                    {key !== "title" && (
                      <span className="text-xs text-fg3 capitalize">{key}</span>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

