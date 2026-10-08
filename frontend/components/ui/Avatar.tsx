import { cn, speakerColor } from "@/lib/colors";
import { initials } from "@/lib/format";

interface AvatarProps {
  id: number;
  name: string;
  size?: "xs" | "sm" | "md";
  className?: string;
}

const sizes = { xs: "h-5 w-5 text-[9px]", sm: "h-7 w-7 text-[11px]", md: "h-8 w-8 text-xs" };

export function Avatar({ id, name, size = "sm", className }: AvatarProps) {
  return (
    <span
      title={name}
      aria-hidden
      className={cn(
        "inline-flex shrink-0 select-none items-center justify-center rounded-full font-semibold text-white",
        sizes[size],
        className,
      )}
      style={{ backgroundColor: speakerColor(id) }}
    >
      {initials(name)}
    </span>
  );
}

export function AvatarStack({
  people,
  max = 4,
}: {
  people: { id: number; name: string }[];
  max?: number;
}) {
  const shown = people.slice(0, max);
  const hidden = people.length - shown.length;
  return (
    <div className="flex items-center" aria-label={people.map((p) => p.name).join(", ")}>
      {shown.map((person) => (
        <Avatar
          key={person.id}
          id={person.id}
          name={person.name}
          className="-ml-0.5 ring-2 ring-surface first:ml-0"
        />
      ))}
      {hidden > 0 && (
        <span className="-ml-0.5 inline-flex h-7 w-7 items-center justify-center rounded-full bg-surface-muted text-[11px] font-semibold text-muted ring-2 ring-surface">
          +{hidden}
        </span>
      )}
    </div>
  );
}
