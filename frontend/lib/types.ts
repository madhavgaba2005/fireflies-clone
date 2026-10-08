// Mirrors the Meeting Service's Pydantic response models (backend/meeting-service/app/schemas).

export type ProcessingStatus = "not_requested" | "pending" | "processing" | "completed" | "failed";
export type MeetingSource = "seed" | "upload" | "paste" | "form";
export type TranscriptFormat = "txt" | "vtt" | "json";

export interface Participant {
  id: number;
  name: string;
  email: string | null;
}

export interface ParticipantWithCount extends Participant {
  meeting_count: number;
}

export interface MeetingListItem {
  id: number;
  title: string;
  meeting_date: string;
  duration_seconds: number;
  source: MeetingSource;
  processing_status: ProcessingStatus;
  participants: Participant[];
  keywords: string[];
  action_item_count: number;
  open_action_item_count: number;
}

export interface MeetingList {
  items: MeetingListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface SpeakerStat {
  participant_id: number;
  name: string;
  talk_time_ms: number;
  percentage: number;
}

export interface MeetingDetail extends MeetingListItem {
  processing_error: string | null;
  transcript_revision: number;
  media_url: string | null;
  created_at: string;
  updated_at: string;
  speaker_stats: SpeakerStat[];
}

export interface Segment {
  id: number;
  sequence: number;
  start_ms: number;
  end_ms: number;
  speaker: { id: number; name: string };
  text: string;
}

export interface Transcript {
  meeting_id: number;
  revision: number;
  segments: Segment[];
}

export interface Topic {
  sequence: number;
  title: string;
  summary: string;
  start_ms: number | null;
}

export interface Summary {
  meeting_id: number;
  overview: string;
  provider: string;
  transcript_revision: number;
  generated_at: string;
  topics: Topic[];
  keywords: string[];
}

export interface ActionItem {
  id: number;
  meeting_id: number;
  title: string;
  description: string | null;
  assignee: Participant | null;
  due_date: string | null;
  completed: boolean;
  completed_at: string | null;
  source: "ai" | "manual";
  start_ms: number | null;
  created_at: string;
  updated_at: string;
}

export interface ParticipantRef {
  id?: number;
  name?: string;
  email?: string;
}

export interface MeetingCreateInput {
  title: string;
  meeting_date: string;
  participants: ParticipantRef[];
  duration_seconds?: number;
  transcript_text?: string;
  transcript_format?: TranscriptFormat;
  source: "upload" | "paste" | "form";
}

export interface MeetingUpdateInput {
  title?: string;
  meeting_date?: string;
  participants?: ParticipantRef[];
}

export interface ActionItemInput {
  title?: string;
  description?: string | null;
  assignee_id?: number | null;
  due_date?: string | null;
  completed?: boolean;
}

export interface MeetingQuery {
  q?: string;
  participantIds?: number[];
  dateFrom?: string;
  dateTo?: string;
  keyword?: string;
  sort?: "-meeting_date" | "meeting_date";
}
