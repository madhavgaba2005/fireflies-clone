"use client";

import { BarChart3, type LucideIcon, Plug, Settings, Upload, Users, Video } from "lucide-react";
import { usePathname } from "next/navigation";

import { useComingSoon } from "@/components/ui/ComingSoon";

import { useOpenCreateMeeting } from "./CreateMeetingContext";

export interface NavEntry {
  label: string;
  icon: LucideIcon;
  href?: string;
  onSelect?: () => void;
  active?: boolean;
  soon?: boolean; // opens a "Coming soon" dialog: out of scope per the assignment
}

/** Primary navigation, shared by the desktop icon rail and the mobile drawer. */
export function usePrimaryNav(): { main: NavEntry[]; footer: NavEntry[] } {
  const pathname = usePathname();
  const comingSoon = useComingSoon();
  const openCreate = useOpenCreateMeeting();
  return {
    main: [
      {
        label: "Meetings",
        icon: Video,
        href: "/meetings",
        active: pathname.startsWith("/meetings"),
      },
      { label: "Uploads", icon: Upload, onSelect: () => openCreate("upload") },
      {
        label: "Analytics",
        icon: BarChart3,
        soon: true,
        onSelect: () =>
          comingSoon({
            name: "Analytics",
            description: "Talk-time trends, topic trackers and meeting insights across your team.",
          }),
      },
      {
        label: "Integrations",
        icon: Plug,
        soon: true,
        onSelect: () =>
          comingSoon({
            name: "Integrations",
            description:
              "Connect Zoom, Google Meet, your calendar and CRM to capture meetings automatically.",
          }),
      },
      {
        label: "Team",
        icon: Users,
        soon: true,
        onSelect: () =>
          comingSoon({
            name: "Team & sharing",
            description: "Invite teammates and share meeting notes and soundbites.",
          }),
      },
    ],
    footer: [
      {
        label: "Settings",
        icon: Settings,
        href: "/settings",
        active: pathname.startsWith("/settings"),
      },
    ],
  };
}
