"use client";

import { X } from "lucide-react";
import { useId, useMemo, useState, type KeyboardEvent } from "react";

import { Avatar } from "@/components/ui/Avatar";
import { useParticipants } from "@/hooks/queries";

export interface PersonChip {
  id?: number; // existing participant
  name: string;
}

/** Chips input: type a name and press Enter (or pick a suggestion from the workspace). */
export function ParticipantsInput({
  value,
  onChange,
}: {
  value: PersonChip[];
  onChange: (next: PersonChip[]) => void;
}) {
  const inputId = useId();
  const [text, setText] = useState("");
  const [focused, setFocused] = useState(false);
  const { data: everyone = [] } = useParticipants();

  const chosen = useMemo(() => new Set(value.map((p) => p.name.toLowerCase())), [value]);
  const suggestions = useMemo(() => {
    const needle = text.trim().toLowerCase();
    return everyone
      .filter(
        (p) =>
          !chosen.has(p.name.toLowerCase()) && (!needle || p.name.toLowerCase().includes(needle)),
      )
      .slice(0, 6);
  }, [everyone, chosen, text]);

  const add = (person: PersonChip) => {
    const name = person.name.trim();
    if (!name || chosen.has(name.toLowerCase())) return;
    const existing = everyone.find((p) => p.name.toLowerCase() === name.toLowerCase());
    onChange([...value, existing ? { id: existing.id, name: existing.name } : { ...person, name }]);
    setText("");
  };

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if ((event.key === "Enter" || event.key === ",") && text.trim()) {
      event.preventDefault();
      add({ name: text });
    } else if (event.key === "Backspace" && !text && value.length) {
      onChange(value.slice(0, -1));
    }
  };

  return (
    <div className="relative">
      <label htmlFor={inputId} className="mb-1.5 block text-[13px] font-medium">
        Participants
      </label>
      <div className="flex min-h-10 flex-wrap items-center gap-1.5 rounded-lg border border-border bg-surface px-2 py-1.5 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary-ring">
        {value.map((person, index) => (
          <span
            key={person.name}
            className="inline-flex items-center gap-1 rounded-full bg-surface-muted py-0.5 pl-0.5 pr-1.5 text-[12px]"
          >
            <Avatar id={person.id ?? index + 1000} name={person.name} size="xs" />
            {person.name}
            <button
              type="button"
              aria-label={`Remove ${person.name}`}
              onClick={() => onChange(value.filter((p) => p.name !== person.name))}
              className="rounded-full text-subtle hover:text-text"
            >
              <X size={12} />
            </button>
          </span>
        ))}
        <input
          id={inputId}
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={onKeyDown}
          onFocus={() => setFocused(true)}
          onBlur={() => setTimeout(() => setFocused(false), 120)}
          placeholder={value.length ? "" : "Type a name and press Enter"}
          className="min-w-32 flex-1 bg-transparent py-1 text-[13px] outline-none"
        />
      </div>
      {focused && suggestions.length > 0 && (
        <ul
          role="listbox"
          aria-label="Suggested participants"
          className="absolute z-10 mt-1 max-h-56 w-full overflow-y-auto rounded-lg border border-border bg-surface p-1 shadow-lg"
        >
          {suggestions.map((person) => (
            <li key={person.id} role="option" aria-selected={false}>
              <button
                type="button"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => add({ id: person.id, name: person.name })}
                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[13px] hover:bg-surface-muted"
              >
                <Avatar id={person.id} name={person.name} size="xs" />
                {person.name}
                {person.email && (
                  <span className="ml-auto text-[11px] text-subtle">{person.email}</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function toParticipantRefs(people: PersonChip[]) {
  return people.map((p) => (p.id ? { id: p.id } : { name: p.name }));
}
