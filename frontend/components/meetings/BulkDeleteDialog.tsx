"use client";

import { Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { errorMessage } from "@/components/ui/States";
import { useDeleteMeeting } from "@/hooks/queries";

/** Deletes the selected meetings one by one with the existing endpoint; reports partial failures. */
export function BulkDeleteDialog({
  meetings,
  onClose,
  onDone,
}: {
  meetings: { id: number; title: string }[];
  onClose: () => void;
  onDone: (deletedIds: number[]) => void;
}) {
  const remove = useDeleteMeeting();
  const [working, setWorking] = useState(false);
  const count = meetings.length;
  const noun = count === 1 ? "meeting" : "meetings";

  const confirm = async () => {
    setWorking(true);
    const deleted: number[] = [];
    let failure: unknown = null;
    for (const meeting of meetings) {
      try {
        await remove.mutateAsync(meeting.id);
        deleted.push(meeting.id);
      } catch (caught) {
        failure = caught;
      }
    }
    setWorking(false);
    if (failure) {
      toast.error(`Deleted ${deleted.length} of ${count} ${noun}`, {
        description: errorMessage(failure),
      });
    } else {
      toast.success(`${count} ${noun} deleted`);
    }
    onDone(deleted);
  };

  return (
    <Modal
      open
      onOpenChange={(open) => !open && !working && onClose()}
      title={`Delete ${count} ${noun}?`}
      size="sm"
      footer={
        <>
          <Button size="sm" onClick={onClose} disabled={working}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" onClick={confirm} disabled={working}>
            {working && <Loader2 size={14} className="animate-spin" />}
            Delete
          </Button>
        </>
      }
    >
      <p className="text-[13.5px] text-muted">
        Their transcripts, notes and action items are deleted too. This can&apos;t be undone.
      </p>
      <ul className="mt-3 max-h-40 list-disc space-y-0.5 overflow-y-auto pl-5 text-[13px]">
        {meetings.map((meeting) => (
          <li key={meeting.id}>{meeting.title}</li>
        ))}
      </ul>
    </Modal>
  );
}
