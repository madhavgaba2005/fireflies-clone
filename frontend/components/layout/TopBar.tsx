"use client";

import { Menu as MenuIcon, Plus, Radio, UserPlus } from "lucide-react";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/Button";
import { useComingSoon } from "@/components/ui/ComingSoon";

import { useOpenCreateMeeting } from "./CreateMeetingContext";
import { GlobalSearch } from "./GlobalSearch";
import { NotificationsButton, UserMenu } from "./UserControls";

/** Toolbar label for the current route; the library's label is its page heading (h1). */
function pageLabel(pathname: string): { text: string; heading: boolean } {
  if (pathname === "/meetings") return { text: "Meetings", heading: true };
  if (pathname.startsWith("/meetings")) return { text: "Meetings", heading: false };
  if (pathname.startsWith("/settings")) return { text: "Settings", heading: false };
  return { text: "Lumen", heading: false };
}

export function TopBar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const pathname = usePathname();
  const openCreate = useOpenCreateMeeting();
  const comingSoon = useComingSoon();
  const label = pageLabel(pathname);
  const Label = label.heading ? "h1" : "p";
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-surface px-3 sm:px-4 lg:px-5">
      <Button
        variant="ghost"
        size="icon"
        className="md:hidden"
        onClick={onOpenMenu}
        aria-label="Open navigation"
      >
        <MenuIcon size={18} />
      </Button>
      <Label className="shrink-0 text-[14px] font-medium text-text md:w-24 xl:w-36">
        {label.text}
      </Label>
      <GlobalSearch />
      <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
        {/* Wrappers control visibility: a class on Button itself would fight its own inline-flex. */}
        <div className="hidden md:block">
          <button
            type="button"
            onClick={() =>
              comingSoon({
                name: "Invite teammates",
                description: "Invite colleagues to your workspace and share meetings with them.",
              })
            }
            className="inline-flex h-8 items-center gap-1.5 rounded-lg bg-primary-soft px-3 text-[13px] font-medium text-primary transition hover:bg-primary-soft/70"
          >
            <UserPlus size={15} /> Invite
          </button>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => openCreate("upload")}
          aria-label="New meeting"
        >
          <Plus size={16} /> <span className="hidden sm:inline">New meeting</span>
        </Button>
        <div className="hidden items-center gap-0.5 md:flex">
          <Button
            variant="ghost"
            size="icon"
            aria-label="Add to live meeting"
            title="Add to live meeting"
            onClick={() =>
              comingSoon({
                name: "Add to live meeting",
                description:
                  "Paste a Zoom, Google Meet or Teams link and the notetaker joins the call.",
              })
            }
          >
            <Radio size={17} />
          </Button>
          <NotificationsButton />
        </div>
        <UserMenu />
      </div>
    </header>
  );
}
