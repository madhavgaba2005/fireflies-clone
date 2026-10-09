"use client";

import {
  ArrowDownWideNarrow,
  ArrowUpNarrowWide,
  Calendar,
  Check,
  ChevronDown,
  Search,
  Tag,
  Users,
  X,
} from "lucide-react";
import { Popover } from "radix-ui";
import { useEffect, useState } from "react";

import { Avatar } from "@/components/ui/Avatar";
import { useParticipants } from "@/hooks/queries";
import { cn } from "@/lib/colors";
import { DATE_PRESETS, EMPTY_FILTERS, hasActiveFilters, type LibraryFilters } from "@/lib/filters";

const SEARCH_DEBOUNCE_MS = 300;

function FilterButton({
  active,
  children,
  ...props
}: React.ComponentProps<"button"> & { active?: boolean }) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex h-8 items-center gap-1.5 rounded-lg border px-3 text-[13px] font-medium transition-colors",
        active
          ? "border-primary/40 bg-primary-soft text-primary"
          : "border-border bg-surface text-text hover:bg-surface-muted",
      )}
      {...props}
    >
      {children}
    </button>
  );
}

function PopoverPanel({ children }: { children: React.ReactNode }) {
  return (
    <Popover.Portal>
      <Popover.Content
        align="start"
        sideOffset={6}
        className="z-50 w-72 rounded-xl border border-border bg-surface p-2 shadow-lg focus:outline-none"
      >
        {children}
      </Popover.Content>
    </Popover.Portal>
  );
}

export function MeetingFilters({
  filters,
  onChange,
}: {
  filters: LibraryFilters;
  onChange: (next: LibraryFilters) => void;
}) {
  const [text, setText] = useState(filters.q);
  const [personQuery, setPersonQuery] = useState("");
  const { data: people = [] } = useParticipants();

  // Keep the box in sync when the URL changes elsewhere (top-bar search, "Clear filters"):
  // adjust state while rendering instead of in an effect (react.dev "You might not need an effect").
  const [syncedQ, setSyncedQ] = useState(filters.q);
  if (filters.q !== syncedQ) {
    setSyncedQ(filters.q);
    setText(filters.q);
  }

  useEffect(() => {
    if (text === filters.q) return;
    const timer = setTimeout(() => onChange({ ...filters, q: text }), SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [text, filters, onChange]);

  const datePreset = DATE_PRESETS.find((p) => p.value === filters.date)!;
  const selectedPeople = people.filter((p) => filters.participantIds.includes(p.id));
  const visiblePeople = people.filter((p) =>
    p.name.toLowerCase().includes(personQuery.toLowerCase()),
  );

  const togglePerson = (id: number) =>
    onChange({
      ...filters,
      participantIds: filters.participantIds.includes(id)
        ? filters.participantIds.filter((x) => x !== id)
        : [...filters.participantIds, id],
    });

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="relative w-full sm:w-52 xl:w-60">
        <Search
          size={15}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle"
        />
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Search by title"
          aria-label="Search by title"
          className="h-8 w-full rounded-lg border border-border bg-surface pl-9 pr-8 text-[13px] outline-none focus:border-primary focus:ring-2 focus:ring-primary-ring"
        />
        {text && (
          <button
            type="button"
            aria-label="Clear search"
            onClick={() => setText("")}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-subtle hover:text-text"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Phones: the controls scroll sideways in one row instead of stacking. */}
      <div className="flex min-w-0 items-center gap-2 max-sm:-mx-4 max-sm:w-[calc(100%+2rem)] max-sm:overflow-x-auto max-sm:px-4 max-sm:pb-0.5 [&>*]:shrink-0">
        <Popover.Root>
          <Popover.Trigger asChild>
            <FilterButton active={filters.date !== "any"} aria-label="Date filter">
              <Calendar size={15} />
              {filters.date === "custom" && (filters.from || filters.to)
                ? `${filters.from || "…"} → ${filters.to || "…"}`
                : datePreset.label}
              <ChevronDown size={14} className="text-subtle" />
            </FilterButton>
          </Popover.Trigger>
          <PopoverPanel>
            <div role="listbox" aria-label="Date range">
              {DATE_PRESETS.map((preset) => (
                <button
                  key={preset.value}
                  type="button"
                  role="option"
                  aria-selected={filters.date === preset.value}
                  onClick={() => onChange({ ...filters, date: preset.value })}
                  className="flex w-full items-center justify-between rounded-lg px-2.5 py-2 text-left text-[13px] hover:bg-surface-muted"
                >
                  {preset.label}
                  {filters.date === preset.value && <Check size={14} className="text-primary" />}
                </button>
              ))}
            </div>
            {filters.date === "custom" && (
              <div className="mt-2 grid grid-cols-2 gap-2 border-t border-border px-1 pt-3">
                <label className="text-[12px] text-muted">
                  From
                  <input
                    type="date"
                    aria-label="From date"
                    value={filters.from}
                    max={filters.to || undefined}
                    onChange={(event) => onChange({ ...filters, from: event.target.value })}
                    className="mt-1 h-8 w-full rounded-md border border-border px-2 text-[12px] text-text"
                  />
                </label>
                <label className="text-[12px] text-muted">
                  To
                  <input
                    type="date"
                    aria-label="To date"
                    value={filters.to}
                    min={filters.from || undefined}
                    onChange={(event) => onChange({ ...filters, to: event.target.value })}
                    className="mt-1 h-8 w-full rounded-md border border-border px-2 text-[12px] text-text"
                  />
                </label>
              </div>
            )}
          </PopoverPanel>
        </Popover.Root>

        <Popover.Root onOpenChange={() => setPersonQuery("")}>
          <Popover.Trigger asChild>
            <FilterButton
              active={filters.participantIds.length > 0}
              aria-label="Participant filter"
            >
              <Users size={15} />
              {selectedPeople.length === 0
                ? "Participants"
                : selectedPeople.length === 1
                  ? selectedPeople[0].name
                  : `${selectedPeople.length} participants`}
              <ChevronDown size={14} className="text-subtle" />
            </FilterButton>
          </Popover.Trigger>
          <PopoverPanel>
            <input
              autoFocus
              value={personQuery}
              onChange={(event) => setPersonQuery(event.target.value)}
              placeholder="Find a person"
              aria-label="Find a person"
              className="mb-1 h-8 w-full rounded-md border border-border px-2.5 text-[13px] outline-none focus:border-primary"
            />
            <div className="max-h-64 overflow-y-auto">
              {visiblePeople.map((person) => {
                const checked = filters.participantIds.includes(person.id);
                return (
                  <label
                    key={person.id}
                    className="flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] hover:bg-surface-muted"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => togglePerson(person.id)}
                      className="accent-[var(--primary)]"
                    />
                    <Avatar id={person.id} name={person.name} size="xs" />
                    <span className="flex-1">{person.name}</span>
                    <span className="text-[11px] text-subtle">{person.meeting_count}</span>
                  </label>
                );
              })}
              {visiblePeople.length === 0 && (
                <p className="px-2 py-3 text-[12px] text-muted">No one matches.</p>
              )}
            </div>
          </PopoverPanel>
        </Popover.Root>

        <FilterButton
          onClick={() =>
            onChange({ ...filters, sort: filters.sort === "newest" ? "oldest" : "newest" })
          }
          aria-label={`Sort: ${filters.sort === "newest" ? "newest first" : "oldest first"}`}
        >
          {filters.sort === "newest" ? (
            <ArrowDownWideNarrow size={15} />
          ) : (
            <ArrowUpNarrowWide size={15} />
          )}
          {filters.sort === "newest" ? "Newest first" : "Oldest first"}
        </FilterButton>

        {filters.keyword && (
          <span className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-primary/40 bg-primary-soft px-3 text-[13px] font-medium text-primary">
            <Tag size={14} /> {filters.keyword}
            <button
              type="button"
              aria-label="Remove tag filter"
              onClick={() => onChange({ ...filters, keyword: "" })}
            >
              <X size={14} />
            </button>
          </span>
        )}

        {hasActiveFilters(filters) && (
          <button
            type="button"
            onClick={() => onChange({ ...EMPTY_FILTERS, sort: filters.sort })}
            className="h-8 px-2 text-[13px] font-medium text-muted hover:text-text"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
