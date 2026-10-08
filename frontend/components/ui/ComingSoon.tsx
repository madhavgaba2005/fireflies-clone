"use client";

import { Rocket } from "lucide-react";
import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

import { Button } from "./Button";
import { Modal } from "./Modal";

interface Feature {
  name: string;
  description: string;
}

const ComingSoonContext = createContext<(feature: Feature) => void>(() => {});

/** Out-of-scope features (live bot, integrations, team…) open one shared "Coming soon" dialog. */
export function ComingSoonProvider({ children }: { children: ReactNode }) {
  const [feature, setFeature] = useState<Feature | null>(null);
  const show = useCallback((next: Feature) => setFeature(next), []);
  return (
    <ComingSoonContext.Provider value={show}>
      {children}
      <Modal
        open={feature !== null}
        onOpenChange={(open) => !open && setFeature(null)}
        title={feature?.name ?? ""}
        size="sm"
        footer={
          <Button variant="primary" size="sm" onClick={() => setFeature(null)}>
            Got it
          </Button>
        }
      >
        <div className="flex gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary-soft text-primary">
            <Rocket size={18} />
          </div>
          <div>
            <p className="font-semibold">Coming soon</p>
            <p className="mt-1 text-[13px] text-muted">{feature?.description}</p>
          </div>
        </div>
      </Modal>
    </ComingSoonContext.Provider>
  );
}

export function useComingSoon() {
  return useContext(ComingSoonContext);
}
