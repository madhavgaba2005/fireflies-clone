import type { Metadata } from "next";
import { Suspense } from "react";

import { MeetingsLibrary } from "@/components/meetings/MeetingsLibrary";

export const metadata: Metadata = { title: "Meetings" };

export default function MeetingsPage() {
  // useSearchParams (filters in the URL) needs a Suspense boundary for static rendering.
  return (
    <Suspense>
      <MeetingsLibrary />
    </Suspense>
  );
}
