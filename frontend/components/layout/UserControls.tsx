"use client";

import { Bell, LogOut, Moon, Settings, Sun, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { useComingSoon } from "@/components/ui/ComingSoon";
import { Menu, MenuItem, MenuSeparator } from "@/components/ui/Menu";
import { useTheme } from "@/hooks/useTheme";
import { setThemePreference } from "@/lib/theme";

// Authentication is out of scope (PDF): a default user is always "signed in".
export const DEFAULT_USER = { id: 101, name: "Alex Morgan", email: "alex.morgan@northwind.io" };

export function NotificationsButton() {
  const comingSoon = useComingSoon();
  return (
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
  );
}

/** Avatar menu shared by the library toolbar and the meeting toolbar. */
export function UserMenu() {
  const theme = useTheme();
  const router = useRouter();
  return (
    <Menu
      trigger={
        <button type="button" aria-label="Account menu" className="rounded-full outline-offset-2">
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
  );
}
