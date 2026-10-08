import { notFound } from "next/navigation";
import { Suspense } from "react";

import { MeetingWorkspace } from "@/components/workspace/MeetingWorkspace";

export default async function MeetingPage({ params }: PageProps<"/meetings/[id]">) {
  const { id } = await params;
  const meetingId = Number(id);
  if (!Number.isInteger(meetingId) || meetingId < 1) notFound();
  return (
    <Suspense>
      <MeetingWorkspace id={meetingId} />
    </Suspense>
  );
}
