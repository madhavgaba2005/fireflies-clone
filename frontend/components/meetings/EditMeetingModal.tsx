"use client";

import { Loader2 } from "lucide-react";
import { useState, type FormEvent } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { FormError, TextField } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { errorMessage } from "@/components/ui/States";
import { useUpdateMeeting } from "@/hooks/queries";
import { fromDateTimeLocal, toDateTimeLocal } from "@/lib/format";
import type { MeetingListItem } from "@/lib/types";

import { ParticipantsInput, toParticipantRefs, type PersonChip } from "./ParticipantsInput";

export function EditMeetingModal({
  meeting,
  onClose,
}: {
  meeting: MeetingListItem;
  onClose: () => void;
}) {
  const update = useUpdateMeeting(meeting.id);
  const [title, setTitle] = useState(meeting.title);
  const [date, setDate] = useState(() => toDateTimeLocal(meeting.meeting_date));
  const [people, setPeople] = useState<PersonChip[]>(() =>
    meeting.participants.map((p) => ({ id: p.id, name: p.name })),
  );
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    try {
      await update.mutateAsync({
        title,
        meeting_date: fromDateTimeLocal(date),
        participants: toParticipantRefs(people),
      });
      toast.success("Meeting updated");
      onClose();
    } catch (caught) {
      setError(errorMessage(caught));
    }
  };

  return (
    <Modal
      open
      onOpenChange={(open) => !open && onClose()}
      title="Edit meeting"
      footer={
        <>
          <Button size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            type="submit"
            form="edit-meeting"
            disabled={update.isPending}
          >
            {update.isPending && <Loader2 size={14} className="animate-spin" />}
            Save changes
          </Button>
        </>
      }
    >
      <form id="edit-meeting" onSubmit={submit} className="flex flex-col gap-4">
        <TextField
          label="Title"
          required
          maxLength={200}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <TextField
          label="Date & time"
          type="datetime-local"
          required
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <ParticipantsInput value={people} onChange={setPeople} />
        <FormError message={error} />
      </form>
    </Modal>
  );
}
