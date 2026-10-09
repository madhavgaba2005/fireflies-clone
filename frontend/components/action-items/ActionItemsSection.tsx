"use client";

import { CheckSquare, Loader2, Plus } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";

import { Avatar } from "@/components/ui/Avatar";
import { Button } from "@/components/ui/Button";
import { ErrorState, Skeleton, errorMessage } from "@/components/ui/States";
import { useActionItems, useCreateActionItem } from "@/hooks/queries";
import type { ActionItem, MeetingDetail } from "@/lib/types";

import { ActionItemEditor, type ActionItemDraft } from "./ActionItemEditor";
import { ActionItemRow } from "./ActionItemRow";

/** Fireflies groups action items by the person responsible. */
export function groupByAssignee(items: ActionItem[]) {
  const groups = new Map<
    string,
    { key: string; name: string; id: number | null; items: ActionItem[] }
  >();
  for (const item of items) {
    const key = item.assignee ? `p${item.assignee.id}` : "unassigned";
    if (!groups.has(key)) {
      groups.set(key, {
        key,
        name: item.assignee?.name ?? "Unassigned",
        id: item.assignee?.id ?? null,
        items: [],
      });
    }
    groups.get(key)!.items.push(item);
  }
  // Named people first (alphabetical), then unassigned.
  return [...groups.values()].sort((a, b) =>
    a.id === null ? 1 : b.id === null ? -1 : a.name.localeCompare(b.name),
  );
}

export function ActionItemsSection({
  meeting,
  onSeek,
}: {
  meeting: MeetingDetail;
  onSeek: (ms: number) => void;
}) {
  const { data: items, isPending, isError, error, refetch } = useActionItems(meeting.id);
  const create = useCreateActionItem(meeting.id);
  const [adding, setAdding] = useState(false);
  const groups = useMemo(() => groupByAssignee(items ?? []), [items]);
  const open = items?.filter((item) => !item.completed).length ?? 0;

  const add = async (draft: ActionItemDraft) => {
    try {
      await create.mutateAsync({
        title: draft.title,
        assignee_id: draft.assigneeId,
        due_date: draft.dueDate || null,
      });
      toast.success("Action item added");
      setAdding(false);
    } catch (caught) {
      toast.error("Couldn't add the action item", { description: errorMessage(caught) });
    }
  };

  return (
    <section className="py-4" aria-label="Action items">
      <div className="mb-2 flex items-center gap-2">
        <CheckSquare size={15} className="text-primary" />
        <h3 className="text-[14px] font-semibold text-text">Action items</h3>
        {items && items.length > 0 && (
          <span className="text-[12px] text-muted">
            {open} open · {items.length - open} done
          </span>
        )}
        <Button
          size="sm"
          variant="ghost"
          className="ml-auto"
          onClick={() => setAdding(true)}
          disabled={adding}
        >
          <Plus size={14} /> Add
        </Button>
      </div>

      {adding && (
        <ActionItemEditor
          participants={meeting.participants}
          saving={create.isPending}
          submitLabel="Add"
          onSubmit={add}
          onCancel={() => setAdding(false)}
        />
      )}

      {isPending ? (
        <div className="space-y-2">
          <Skeleton className="h-8 w-full" />
          <Skeleton className="h-8 w-full" />
        </div>
      ) : isError ? (
        <ErrorState
          error={error}
          title="Couldn't load action items"
          onRetry={() => refetch()}
          className="py-6"
        />
      ) : items.length === 0 ? (
        !adding && (
          <p className="py-2 text-[13px] text-muted">
            No action items yet. Add one to keep track of follow-ups.
          </p>
        )
      ) : (
        <div className="space-y-3">
          {groups.map((group) => (
            <div key={group.key}>
              <div className="mb-1 flex items-center gap-2 text-[12px] font-semibold text-muted">
                {group.id !== null && <Avatar id={group.id} name={group.name} size="xs" />}
                {group.name}
              </div>
              <ul className="space-y-0.5">
                {group.items.map((item) => (
                  <ActionItemRow key={item.id} item={item} meeting={meeting} onSeek={onSeek} />
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
      {create.isPending && !adding && <Loader2 size={14} className="animate-spin text-muted" />}
    </section>
  );
}
