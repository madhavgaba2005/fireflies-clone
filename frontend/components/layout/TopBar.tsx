"use client";

import { LogOut, Menu as MenuIcon, Plus, Radio, Settings, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { useComingSoon } from "@/components/ui/ComingSoon";
import { Menu, MenuItem, MenuSeparator } from "@/components/ui/Menu";

import { useOpenCreateMeeting } from "./CreateMeetingContext";
import { GlobalSearch } from "./GlobalSearch";

// Authentication is out of scope (PDF): a default user is always "signed in".
export const DEFAULT_USER = { id: 101, name: "Alex Morgan", email: "alex.morgan@northwind.io" };

export function TopBar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const router = useRouter();
  const openCreate = useOpenCreateMeeting();
  const comingSoon = useComingSoon();
  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-surface px-4">
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden"
        onClick={onOpenMenu}
        aria-label="Open navigation"
      >
        <MenuIcon size={18} />
      </Button>
      <GlobalSearch />
      <div className="ml-auto flex items-center gap-2">
        {/* Wrapper controls visibility: a class on Button itself would fight its own inline-flex. */}
        <div className="hidden md:block">
          <Button
            size="sm"
            onClick={() =>
              comingSoon({
                name: "Add to live meeting",
                description:
                  "Paste a Zoom, Google Meet or Teams link and the notetaker joins the call.",
              })
            }
          >
            <Radio size={15} /> Add to live meeting
          </Button>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={() => openCreate("upload")}
          aria-label="New meeting"
        >
          <Plus size={16} /> <span className="hidden sm:inline">New meeting</span>
        </Button>
        <Menu
          trigger={
            <button
              type="button"
              aria-label="Account menu"
              className="rounded-full outline-offset-2"
            >
              <Avatar id={DEFAULT_USER.id} name={DEFAULT_USER.name} size="md" />
            </button>
          }
        >
          <div className="px-2.5 py-2">
            <p className="text-[13px] font-semibold">{DEFAULT_USER.name}</p>
            <p className="text-[12px] text-muted">{DEFAULT_USER.email}</p>
          </div>
          <MenuSeparator />
          <MenuItem icon={<User size={15} />} onSelect={() => router.push("/settings?tab=profile")}>
            Profile
          </MenuItem>
          <MenuItem icon={<Settings size={15} />} onSelect={() => router.push("/settings")}>
            Settings
          </MenuItem>
          <MenuSeparator />
          <MenuItem
            icon={<LogOut size={15} />}
            onSelect={() =>
              toast.info("Sign-in is out of scope — you're always signed in as the demo user.")
            }
          >
            Sign out
          </MenuItem>
        </Menu>
      </div>
    </header>
  );
}
