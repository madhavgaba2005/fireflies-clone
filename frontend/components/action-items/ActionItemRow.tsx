"use client";

import { CalendarDays, Pencil, Sparkles, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { errorMessage } from "@/components/ui/States";
import { useDeleteActionItem, useUpdateActionItem } from "@/hooks/queries";
import { cn } from "@/lib/colors";
import { isoDay } from "@/lib/filters";
import { formatTimestamp } from "@/lib/format";
import type { ActionItem, MeetingDetail } from "@/lib/types";

import { ActionItemEditor, type ActionItemDraft } from "./ActionItemEditor";

function dueLabel(due: string): string {
  return new Date(`${due}T00:00:00`).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });
}

export function ActionItemRow({
  item,
  meeting,
  onSeek,
}: {
  item: ActionItem;
  meeting: MeetingDetail;
  onSeek: (ms: number) => void;
}) {
  const update = useUpdateActionItem(meeting.id);
  const remove = useDeleteActionItem(meeting.id);
  const [editing, setEditing] = useState(false);
  // Optimistic checkbox: set synchronously on click so it never flickers back, cleared once the
  // server answers (the refetched item then carries the real value) or rolled back on error.
  const [optimisticDone, setOptimisticDone] = useState<boolean | null>(null);
  const completed = optimisticDone ?? item.completed;
  const overdue = !completed && item.due_date !== null && item.due_date < isoDay(new Date());

  // mutateAsync + await: unlike mutate()'s per-call callbacks, the promise still settles if this
  // row unmounts first (e.g. the list refetches after a delete), so the toast always shows.
  const toggle = async () => {
    setOptimisticDone(!completed);
    try {
      await update.mutateAsync({ id: item.id, input: { completed: !completed } });
    } catch (error) {
      toast.error("Couldn't update the action item", { description: errorMessage(error) });
    } finally {
      setOptimisticDone(null);
    }
  };

  const save = async (draft: ActionItemDraft) => {
    try {
      await update.mutateAsync({
        id: item.id,
        input: {
          title: draft.title,
          assignee_id: draft.assigneeId,
          due_date: draft.dueDate || null,
        },
      });
      toast.success("Action item updated");
      setEditing(false);
    } catch (error) {
      toast.error("Couldn't save", { description: errorMessage(error) });
    }
  };

  const destroy = async () => {
    try {
      await remove.mutateAsync(item.id);
      toast.success("Action item deleted");
    } catch (error) {
      toast.error("Couldn't delete", { description: errorMessage(error) });
    }
  };

  if (editing) {
    return (
      <li>
        <ActionItemEditor
          participants={meeting.participants}
          initial={{
            title: item.title,
            assigneeId: item.assignee?.id ?? null,
            dueDate: item.due_date ?? "",
          }}
          saving={update.isPending}
          submitLabel="Save"
          onSubmit={save}
          onCancel={() => setEditing(false)}
        />
      </li>
    );
  }

  return (
    <li
      data-testid="action-item"
      className="group flex items-start gap-2.5 rounded-lg px-1.5 py-1.5 hover:bg-surface-muted"
    >
      <input
        type="checkbox"
        checked={completed}
        onChange={toggle}
        aria-label={`Mark “${item.title}” as ${completed ? "not done" : "done"}`}
        className="mt-0.5 h-4 w-4 shrink-0 cursor-pointer accent-[var(--primary)]"
      />
      <div className="min-w-0 flex-1">
        <p className={cn("text-[13.5px] leading-snug", completed && "text-subtle line-through")}>
          {item.title}
        </p>
        <div className="mt-0.5 flex flex-wrap items-center gap-x-2.5 text-[11.5px] text-muted">
          {item.due_date && (
            <span
              className={cn("inline-flex items-center gap-1", overdue && "font-medium text-danger")}
            >
              <CalendarDays size={11} /> {overdue ? "Overdue · " : ""}
              {dueLabel(item.due_date)}
            </span>
          )}
          {item.start_ms !== null && (
            <button
              type="button"
              onClick={() => onSeek(item.start_ms!)}
              className="tabular font-medium text-primary hover:underline"
              aria-label={`Jump to ${formatTimestamp(item.start_ms)}`}
            >
              {formatTimestamp(item.start_ms)}
            </button>
          )}
          {item.source === "ai" && (
            <span className="inline-flex items-center gap-0.5" title="Extracted by AI">
              <Sparkles size={11} /> AI
            </span>
          )}
        </div>
      </div>
      <div className="flex shrink-0 gap-0.5 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100">
        <button
          type="button"
          onClick={() => setEditing(true)}
          aria-label={`Edit “${item.title}”`}
          className="rounded p-1 text-subtle hover:bg-surface hover:text-text"
        >
          <Pencil size={13} />
        </button>
        <button
          type="button"
          onClick={destroy}
          disabled={remove.isPending}
          aria-label={`Delete “${item.title}”`}
          className="rounded p-1 text-subtle hover:bg-surface hover:text-danger"
        >
          <Trash2 size={13} />
        </button>
      </div>
    </li>
  );
}
