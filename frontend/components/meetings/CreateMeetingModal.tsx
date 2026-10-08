"use client";

import { ClipboardPaste, FileText, FileUp, Loader2, PencilLine } from "lucide-react";
import { useRouter } from "next/navigation";
import { useRef, useState, type FormEvent } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/Button";
import { FormError, TextArea, TextField } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { errorMessage } from "@/components/ui/States";
import { useCreateMeeting } from "@/hooks/queries";
import { cn } from "@/lib/colors";
import { fromDateTimeLocal, toDateTimeLocal } from "@/lib/format";
import type { MeetingCreateInput, TranscriptFormat } from "@/lib/types";

import { ParticipantsInput, toParticipantRefs, type PersonChip } from "./ParticipantsInput";

export type CreateTab = "upload" | "paste" | "form";

const TABS: { id: CreateTab; label: string; icon: typeof FileUp }[] = [
  { id: "upload", label: "Upload file", icon: FileUp },
  { id: "paste", label: "Paste transcript", icon: ClipboardPaste },
  { id: "form", label: "Manual entry", icon: PencilLine },
];

const MAX_FILE_BYTES = 1_000_000;
const EXAMPLE =
  "[00:00] Priya: Let's begin today's meeting.\n[00:18] Sarah: The launch is scheduled for November.";

export function formatFromFileName(name: string): TranscriptFormat {
  const extension = name.toLowerCase().split(".").pop();
  return extension === "vtt" ? "vtt" : extension === "json" ? "json" : "txt";
}

function titleFromFileName(name: string): string {
  const base = name
    .replace(/\.[^.]+$/, "")
    .replace(/[-_]+/g, " ")
    .trim();
  return base ? base[0].toUpperCase() + base.slice(1) : "";
}

export function CreateMeetingModal({
  initialTab,
  onClose,
}: {
  initialTab: CreateTab;
  onClose: () => void;
}) {
  const router = useRouter();
  const create = useCreateMeeting();
  const fileInput = useRef<HTMLInputElement>(null);
  const [tab, setTab] = useState<CreateTab>(initialTab);
  const [title, setTitle] = useState("");
  const [date, setDate] = useState(() => toDateTimeLocal(new Date()));
  const [people, setPeople] = useState<PersonChip[]>([]);
  const [pasted, setPasted] = useState("");
  const [file, setFile] = useState<{ name: string; text: string } | null>(null);
  const [minutes, setMinutes] = useState("30");
  const [error, setError] = useState<string | null>(null);

  const chooseFile = async (selected: File | undefined) => {
    setError(null);
    if (!selected) return;
    if (selected.size > MAX_FILE_BYTES) {
      setError(
        "That file is larger than 1 MB. Transcripts are text — try a .txt, .vtt or .json export.",
      );
      return;
    }
    setFile({ name: selected.name, text: await selected.text() });
    if (!title) setTitle(titleFromFileName(selected.name));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    const input: MeetingCreateInput = {
      title,
      meeting_date: fromDateTimeLocal(date),
      participants: toParticipantRefs(people),
      source: tab,
    };
    if (tab === "upload") {
      if (!file) return setError("Choose a transcript file to upload.");
      input.transcript_text = file.text;
      input.transcript_format = formatFromFileName(file.name);
    } else if (tab === "paste") {
      if (!pasted.trim())
        return setError("Paste a transcript, or use Manual entry to add a meeting without one.");
      input.transcript_text = pasted;
      input.transcript_format = "txt";
    } else {
      input.duration_seconds = Math.max(0, Math.round(Number(minutes || 0) * 60));
    }
    try {
      const meeting = await create.mutateAsync(input);
      toast.success("Meeting created", {
        description: input.transcript_text ? "Lumen is generating your notes…" : undefined,
      });
      onClose();
      router.push(`/meetings/${meeting.id}`);
    } catch (caught) {
      setError(errorMessage(caught));
    }
  };

  return (
    <Modal
      open
      onOpenChange={(open) => !open && onClose()}
      title="New meeting"
      description="Upload or paste a transcript and Lumen writes the notes — or add a meeting manually."
      size="lg"
      footer={
        <>
          <Button size="sm" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            type="submit"
            form="create-meeting"
            disabled={create.isPending}
          >
            {create.isPending && <Loader2 size={14} className="animate-spin" />}
            Create meeting
          </Button>
        </>
      }
    >
      <form id="create-meeting" onSubmit={submit} className="flex flex-col gap-4">
        <div
          role="tablist"
          aria-label="How to add the meeting"
          className="grid grid-cols-3 gap-1 rounded-xl bg-surface-muted p-1"
        >
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              role="tab"
              aria-selected={tab === id}
              onClick={() => {
                setTab(id);
                setError(null);
              }}
              className={cn(
                "flex items-center justify-center gap-1.5 rounded-lg py-2 text-[13px] font-medium transition",
                tab === id ? "bg-surface text-text shadow-sm" : "text-muted hover:text-text",
              )}
            >
              <Icon size={15} /> {label}
            </button>
          ))}
        </div>

        {tab === "upload" && (
          <div>
            <input
              ref={fileInput}
              type="file"
              accept=".txt,.vtt,.json,text/plain,text/vtt,application/json"
              className="sr-only"
              aria-label="Transcript file"
              onChange={(event) => chooseFile(event.target.files?.[0])}
            />
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                chooseFile(event.dataTransfer.files[0]);
              }}
              className="flex w-full flex-col items-center rounded-xl border-2 border-dashed border-border px-4 py-7 text-center transition hover:border-primary hover:bg-primary-soft/40"
            >
              {file ? (
                <>
                  <FileText size={22} className="text-primary" />
                  <span className="mt-2 text-[13px] font-semibold">{file.name}</span>
                  <span className="text-[12px] text-muted">
                    {formatFromFileName(file.name).toUpperCase()} · {file.text.split("\n").length}{" "}
                    lines · click to change
                  </span>
                </>
              ) : (
                <>
                  <FileUp size={22} className="text-primary" />
                  <span className="mt-2 text-[13px] font-semibold">
                    Drop a transcript here or click to browse
                  </span>
                  <span className="text-[12px] text-muted">.txt, .vtt or .json — up to 1 MB</span>
                </>
              )}
            </button>
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-[1fr_200px]">
          <TextField
            label="Title"
            required
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Weekly product sync"
          />
          <TextField
            label="Date & time"
            type="datetime-local"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>

        <ParticipantsInput value={people} onChange={setPeople} />

        {tab === "paste" && (
          <TextArea
            label="Transcript"
            rows={8}
            value={pasted}
            onChange={(e) => setPasted(e.target.value)}
            placeholder={EXAMPLE}
            hint={
              <>
                One line per utterance:{" "}
                <code className="rounded bg-surface-muted px-1">[mm:ss] Speaker: text</code>.
                Speakers are added as participants automatically.
              </>
            }
          />
        )}

        {tab === "form" && (
          <TextField
            label="Duration (minutes)"
            type="number"
            min={0}
            max={1440}
            value={minutes}
            onChange={(e) => setMinutes(e.target.value)}
            hint="No transcript yet — you can still add action items."
          />
        )}

        <FormError message={error} />
      </form>
    </Modal>
  );
}
