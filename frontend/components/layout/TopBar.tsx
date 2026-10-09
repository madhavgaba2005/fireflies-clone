"use client";

import {
  Bell,
  LogOut,
  Menu as MenuIcon,
  Moon,
  Plus,
  Radio,
  Settings,
  Sun,
  User,
  UserPlus,
} from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";

import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { useComingSoon } from "@/components/ui/ComingSoon";
import { Menu, MenuItem, MenuSeparator } from "@/components/ui/Menu";
import { useTheme } from "@/hooks/useTheme";
import { setThemePreference } from "@/lib/theme";

import { useOpenCreateMeeting } from "./CreateMeetingContext";
import { GlobalSearch } from "./GlobalSearch";

// Authentication is out of scope (PDF): a default user is always "signed in".
export const DEFAULT_USER = { id: 101, name: "Alex Morgan", email: "alex.morgan@northwind.io" };

/** Toolbar label for the current route; the library's label is its page heading (h1). */
function pageLabel(pathname: string): { text: string; heading: boolean } {
  if (pathname === "/meetings") return { text: "Meetings", heading: true };
  if (pathname.startsWith("/meetings")) return { text: "Meetings", heading: false };
  if (pathname.startsWith("/settings")) return { text: "Settings", heading: false };
  return { text: "Lumen", heading: false };
}

export function TopBar({ onOpenMenu }: { onOpenMenu: () => void }) {
  const theme = useTheme();
  const router = useRouter();
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
          <Button
            variant="ghost"
            size="icon"
            aria-label="Notifications"
            title="Notifications"
            onClick={() =>
              comingSoon({
                name: "Notifications",
                description: "Get notified when notes are ready or a teammate shares a meeting.",
              })
            }
          >
            <Bell size={17} />
          </Button>
        </div>
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
          <MenuItem
            icon={theme === "dark" ? <Sun size={15} /> : <Moon size={15} />}
            onSelect={() => setThemePreference(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? "Light mode" : "Dark mode"}
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
