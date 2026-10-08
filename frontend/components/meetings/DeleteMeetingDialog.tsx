"use client";

import { Loader2 } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { errorMessage } from "@/components/ui/States";
import { useDeleteMeeting } from "@/hooks/queries";

export function DeleteMeetingDialog({
  meeting,
  onClose,
  onDeleted,
}: {
  meeting: { id: number; title: string };
  onClose: () => void;
  onDeleted?: () => void;
}) {
  const remove = useDeleteMeeting();

  const confirm = async () => {
    try {
      await remove.mutateAsync(meeting.id);
      toast.success("Meeting deleted", { description: meeting.title });
      onClose();
      onDeleted?.();
    } catch (caught) {
      toast.error("Couldn't delete the meeting", { description: errorMessage(caught) });
    }
  };

  return (
    <Modal
      open
      onOpenChange={(open) => !open && onClose()}
      title="Delete meeting?"
      size="sm"
      footer={
        <>
          <Button size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button variant="danger" size="sm" onClick={confirm} disabled={remove.isPending}>
            {remove.isPending && <Loader2 size={14} className="animate-spin" />}
            Delete
          </Button>
        </>
      }
    >
      <p className="text-[13px] text-muted">
        <span className="font-semibold text-text">{meeting.title}</span> and its transcript, notes
        and action items will be permanently deleted.
      </p>
    </Modal>
  );
}
