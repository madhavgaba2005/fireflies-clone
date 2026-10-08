import { Maximize2, Minimize2 } from "lucide-react";

/** Desktop-only: focus one workspace panel at full width (mobile already shows one panel at a time). */
export function PanelExpandButton({
  panel,
  expanded,
  onToggle,
}: {
  panel: string;
  expanded: boolean;
  onToggle: () => void;
}) {
  const label = expanded ? `Show both panels` : `Expand ${panel}`;
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-label={label}
      aria-pressed={expanded}
      title={label}
      className="hidden h-8 w-8 shrink-0 items-center justify-center rounded-lg text-muted transition hover:bg-surface-muted hover:text-text lg:inline-flex"
    >
      {expanded ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
    </button>
  );
}
