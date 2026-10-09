"use client";

import { Building2, Hash, LayoutList, Plus, Share2 } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useComingSoon } from "@/components/ui/ComingSoon";
import { cn } from "@/lib/colors";

const itemClass = (active = false) =>
  cn(
    "flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-[13.5px] transition-colors",
    "focus-visible:outline-2 focus-visible:outline-primary",
    active
      ? "bg-primary-soft font-medium text-primary"
      : "text-muted hover:bg-surface-muted hover:text-text",
  );

/**
 * Contextual Meetings navigation (Fireflies' second sidebar). Only real views are links; sharing and
 * channels are team features, out of scope per the assignment, so they open "Coming soon".
 */
export function MeetingsSidebar({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const comingSoon = useComingSoon();
  const soon = (name: string, description: string) => () => {
    onNavigate?.();
    comingSoon({ name, description });
  };
  const channels = soon("Channels", "Group meetings into channels and share them with your team.");

  return (
    <nav aria-label="Meetings" className="flex h-full w-full flex-col bg-surface">
      <div className="flex h-14 shrink-0 items-center gap-2.5 border-b border-border px-4">
        <span className="flex h-7 w-7 items-center justify-center rounded-md bg-surface-muted text-meta">
          <Building2 size={15} />
        </span>
        <div className="min-w-0 leading-tight">
          <p className="truncate text-[13px] font-semibold">Northwind</p>
          <p className="text-[11.5px] text-meta">Workspace</p>
        </div>
      </div>

      <div className="flex flex-col gap-0.5 p-2.5">
        <Link
          href="/meetings"
          onClick={onNavigate}
          aria-current={pathname === "/meetings" ? "page" : undefined}
          className={itemClass(pathname === "/meetings")}
        >
          <LayoutList size={16} /> All meetings
        </Link>
        <button
          type="button"
          className={itemClass()}
          onClick={soon("Shared with me", "Meetings your teammates share with you appear here.")}
        >
          <Share2 size={16} /> Shared with me
          <span className="ml-auto rounded bg-surface-muted px-1.5 py-0.5 text-[10px] text-meta">
            Soon
          </span>
        </button>
      </div>

      <div className="mx-2.5 border-t border-border" />

      <div className="p-2.5">
        <div className="flex items-center justify-between px-2.5 py-1.5">
          <p className="text-[12.5px] font-medium text-text">Channels</p>
          <button
            type="button"
            aria-label="New channel"
            onClick={channels}
            className="rounded p-0.5 text-meta hover:bg-surface-muted hover:text-text"
          >
            <Plus size={15} />
          </button>
        </div>
        <div className="flex flex-col items-center px-3 py-5 text-center">
          <Hash size={18} className="text-primary/70" />
          <p className="mt-2 text-[12.5px] text-muted">
            Create channels to organize your conversations
          </p>
          <button
            type="button"
            onClick={channels}
            className="mt-3 inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2.5 py-1 text-[12.5px] font-medium hover:bg-surface-muted"
          >
            <Plus size={13} /> Channel
          </button>
        </div>
      </div>
    </nav>
  );
}
