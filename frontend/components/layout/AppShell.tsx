"use client";

import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";

import { ComingSoonProvider } from "@/components/ui/ComingSoon";

import { CreateMeetingProvider } from "./CreateMeetingContext";
import { IconRail } from "./IconRail";
import { MeetingsSidebar } from "./MeetingsSidebar";
import { NavDrawer } from "./NavDrawer";
import { TopBar } from "./TopBar";

/**
 * Fireflies-style frame: a narrow icon rail, a contextual Meetings sidebar on the library (desktop),
 * then the toolbar and the page. Phones get a drawer instead of both sidebars.
 */
export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [drawerOpen, setDrawerOpen] = useState(false); // closed by the drawer's own navigation clicks
  const isLibrary = pathname === "/meetings";

  return (
    <ComingSoonProvider>
      <CreateMeetingProvider>
        <div className="flex h-dvh overflow-hidden">
          <div className="hidden md:flex">
            <IconRail />
          </div>
          {isLibrary && (
            <div className="hidden w-[220px] shrink-0 border-r border-border lg:block">
              <MeetingsSidebar />
            </div>
          )}
          {drawerOpen && <NavDrawer onClose={() => setDrawerOpen(false)} />}
          <div className="flex min-w-0 flex-1 flex-col">
            <TopBar onOpenMenu={() => setDrawerOpen(true)} />
            <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
          </div>
        </div>
      </CreateMeetingProvider>
    </ComingSoonProvider>
  );
}
