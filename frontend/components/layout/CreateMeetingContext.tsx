"use client";

import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

import { CreateMeetingModal, type CreateTab } from "@/components/meetings/CreateMeetingModal";

const CreateMeetingContext = createContext<(tab?: CreateTab) => void>(() => {});

/** The "New meeting" dialog can be opened from the top bar, the sidebar or an empty library. */
export function CreateMeetingProvider({ children }: { children: ReactNode }) {
  const [tab, setTab] = useState<CreateTab | null>(null);
  const open = useCallback((initial: CreateTab = "upload") => setTab(initial), []);
  return (
    <CreateMeetingContext.Provider value={open}>
      {children}
      {tab && <CreateMeetingModal initialTab={tab} onClose={() => setTab(null)} />}
    </CreateMeetingContext.Provider>
  );
}

export function useOpenCreateMeeting() {
  return useContext(CreateMeetingContext);
}
