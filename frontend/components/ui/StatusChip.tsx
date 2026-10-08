import { AlertCircle, CheckCircle2, Loader2, Sparkles } from "lucide-react";

import { cn } from "@/lib/colors";
import type { ProcessingStatus } from "@/lib/types";

const config: Record<
  ProcessingStatus,
  { label: string; className: string; icon: typeof Sparkles; spin?: boolean } | null
> = {
  not_requested: null,
  pending: {
    label: "Generating notes",
    className: "bg-primary-soft text-primary",
    icon: Loader2,
    spin: true,
  },
  processing: {
    label: "Generating notes",
    className: "bg-primary-soft text-primary",
    icon: Loader2,
    spin: true,
  },
  completed: {
    label: "Notes ready",
    className: "bg-success-soft text-success",
    icon: CheckCircle2,
  },
  failed: { label: "Notes failed", className: "bg-danger-soft text-danger", icon: AlertCircle },
};

/** Visible state of the asynchronous AI pipeline. `hideCompleted` keeps busy lists calm. */
export function StatusChip({
  status,
  hideCompleted = false,
}: {
  status: ProcessingStatus;
  hideCompleted?: boolean;
}) {
  const entry = config[status];
  if (!entry || (hideCompleted && status === "completed")) return null;
  const Icon = entry.icon;
  return (
    <span
      data-status={status}
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium",
        entry.className,
      )}
    >
      <Icon size={12} className={entry.spin ? "animate-spin" : undefined} />
      {entry.label}
    </span>
  );
}
