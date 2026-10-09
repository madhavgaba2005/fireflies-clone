"use client";

import { X } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/colors";

import { Logo } from "./Logo";
import { MeetingsSidebar } from "./MeetingsSidebar";
import { type NavEntry, usePrimaryNav } from "./navigation";

function DrawerItem({ entry, onNavigate }: { entry: NavEntry; onNavigate: () => void }) {
  const { icon: Icon, label, href, onSelect, active, soon } = entry;
  const className = cn(
    "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-[14px] font-medium",
    active ? "bg-primary-soft text-primary" : "text-muted hover:bg-surface-muted hover:text-text",
  );
  const content = (
    <>
      <Icon size={18} />
      <span className="flex-1 text-left">{label}</span>
      {soon && (
        <span className="rounded bg-surface-muted px-1.5 py-0.5 text-[10px] text-meta">Soon</span>
      )}
    </>
  );
  return href ? (
    <Link
      href={href}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      className={className}
    >
      {content}
    </Link>
  ) : (
    <button
      type="button"
      onClick={() => {
        onNavigate();
        onSelect?.();
      }}
      className={className}
    >
      {content}
    </button>
  );
}

/** Phone navigation: primary items plus the Meetings section, in one drawer. */
export function NavDrawer({ onClose }: { onClose: () => void }) {
  const { main, footer } = usePrimaryNav();
  return (
    <div className="fixed inset-0 z-40 md:hidden" role="dialog" aria-modal aria-label="Navigation">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div className="relative flex h-full w-72 max-w-[85vw] flex-col overflow-y-auto bg-surface shadow-xl">
        <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
          <Logo />
          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation"
            className="rounded-md p-1.5 text-meta hover:bg-surface-muted"
          >
            <X size={18} />
          </button>
        </div>
        <nav aria-label="Main" className="flex flex-col gap-0.5 p-2.5">
          {[...main, ...footer].map((entry) => (
            <DrawerItem key={entry.label} entry={entry} onNavigate={onClose} />
          ))}
        </nav>
        <div className="border-t border-border">
          <MeetingsSidebar onNavigate={onClose} />
        </div>
      </div>
    </div>
  );
}
