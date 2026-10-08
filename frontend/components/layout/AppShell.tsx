"use client";

import { useState, type ReactNode } from "react";

import { ComingSoonProvider } from "@/components/ui/ComingSoon";

import { CreateMeetingProvider } from "./CreateMeetingContext";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

/** Fireflies-style frame: fixed left navigation + top bar; pages render in the remaining space. */
export function AppShell({ children }: { children: ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false); // closed by the drawer's own navigation clicks

  return (
    <ComingSoonProvider>
      <CreateMeetingProvider>
        <div className="flex h-dvh overflow-hidden">
          <div className="hidden lg:block">
            <Sidebar />
          </div>
          {drawerOpen && (
            <div className="fixed inset-0 z-40 lg:hidden">
              <div className="absolute inset-0 bg-black/30" onClick={() => setDrawerOpen(false)} />
              <div className="relative h-full w-60 shadow-xl">
                <Sidebar onNavigate={() => setDrawerOpen(false)} />
              </div>
            </div>
          )}
          <div className="flex min-w-0 flex-1 flex-col">
            <TopBar onOpenMenu={() => setDrawerOpen(true)} />
            <main className="min-h-0 flex-1 overflow-y-auto">{children}</main>
          </div>
        </div>
      </CreateMeetingProvider>
    </ComingSoonProvider>
  );
}
