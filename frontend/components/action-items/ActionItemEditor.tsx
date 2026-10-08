"use client";

import { Loader2 } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import type { Participant } from "@/lib/types";

export interface ActionItemDraft {
  title: string;
  assigneeId: number | null;
  dueDate: string;
}

/** Inline form used both to add and to edit an action item. */
export function ActionItemEditor({
  participants,
  initial = { title: "", assigneeId: null, dueDate: "" },
  saving,
  submitLabel,
  onSubmit,
  onCancel,
}: {
  participants: Participant[];
  initial?: ActionItemDraft;
  saving: boolean;
  submitLabel: string;
  onSubmit: (draft: ActionItemDraft) => void;
  onCancel: () => void;
}) {
  const [draft, setDraft] = useState(initial);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!draft.title.trim() || saving) return; // guards double submits too
    onSubmit({ ...draft, title: draft.title.trim() });
  };

  return (
    <form
      onSubmit={submit}
      onKeyDown={(event) => event.key === "Escape" && onCancel()}
      className="mb-3 rounded-xl border border-primary/30 bg-surface p-3 shadow-sm"
      aria-label={submitLabel === "Add" ? "New action item" : "Edit action item"}
    >
      <input
        autoFocus
        required
        maxLength={500}
        value={draft.title}
        onChange={(event) => setDraft({ ...draft, title: event.target.value })}
        placeholder="What needs to be done?"
        aria-label="Action item"
        className="w-full bg-transparent text-[13.5px] outline-none placeholder:text-subtle"
      />
      <div className="mt-2.5 flex flex-wrap items-center gap-2">
        <select
          aria-label="Assignee"
          value={draft.assigneeId ?? ""}
          onChange={(event) =>
            setDraft({
              ...draft,
              assigneeId: event.target.value ? Number(event.target.value) : null,
            })
          }
          className="h-8 rounded-md border border-border bg-surface px-2 text-[12.5px]"
        >
          <option value="">Unassigned</option>
          {participants.map((person) => (
            <option key={person.id} value={person.id}>
              {person.name}
            </option>
          ))}
        </select>
        <input
          type="date"
          aria-label="Due date"
          value={draft.dueDate}
          onChange={(event) => setDraft({ ...draft, dueDate: event.target.value })}
          className="h-8 rounded-md border border-border bg-surface px-2 text-[12.5px]"
        />
        <div className="ml-auto flex gap-1.5">
          <Button size="sm" variant="ghost" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            size="sm"
            variant="primary"
            type="submit"
            disabled={saving || !draft.title.trim()}
          >
            {saving && <Loader2 size={13} className="animate-spin" />}
            {submitLabel}
          </Button>
        </div>
      </div>
    </form>
  );
}
