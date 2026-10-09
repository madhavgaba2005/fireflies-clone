"use client";

import Link from "next/link";

import { cn } from "@/lib/colors";

import { Logo } from "./Logo";
import { type NavEntry, usePrimaryNav } from "./navigation";

function RailItem({ entry }: { entry: NavEntry }) {
  const { icon: Icon, label, href, onSelect, active, soon } = entry;
  const name = soon ? `${label} (coming soon)` : label;
  const className = cn(
    "group relative flex h-9 w-9 items-center justify-center rounded-lg transition-colors",
    "focus-visible:outline-2 focus-visible:outline-primary",
    active ? "bg-primary-soft text-primary" : "text-meta hover:bg-surface-muted hover:text-text",
  );
  const content = (
    <>
      <Icon size={18} strokeWidth={active ? 2.2 : 1.8} />
      {/* Hover/focus tooltip: the rail shows icons only. */}
      <span
        aria-hidden
        className="pointer-events-none absolute left-full z-50 ml-2 whitespace-nowrap rounded-md bg-text px-2 py-1 text-[12px] font-medium text-bg opacity-0 shadow-md transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100"
      >
        {label}
        {soon && " · Soon"}
      </span>
    </>
  );
  return href ? (
    <Link
      href={href}
      aria-label={name}
      aria-current={active ? "page" : undefined}
      className={className}
    >
      {content}
    </Link>
  ) : (
    <button type="button" aria-label={name} onClick={onSelect} className={className}>
      {content}
    </button>
  );
}

/** Narrow primary navigation (desktop and tablet). Phones use NavDrawer instead. */
export function IconRail() {
  const { main, footer } = usePrimaryNav();
  return (
    <nav
      aria-label="Main"
      className="flex h-full w-12 shrink-0 flex-col items-center gap-1 border-r border-border bg-rail py-3"
    >
      <div className="mb-3">
        <Logo compact />
      </div>
      {main.map((entry) => (
        <RailItem key={entry.label} entry={entry} />
      ))}
      <div className="mt-auto flex flex-col items-center gap-1">
        {footer.map((entry) => (
          <RailItem key={entry.label} entry={entry} />
        ))}
      </div>
    </nav>
  );
}
