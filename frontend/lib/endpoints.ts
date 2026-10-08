// One typed function per Meeting Service endpoint (see docs/API.md).
import { apiFetch } from "./api";
import type {
  ActionItem,
  ActionItemInput,
  MeetingCreateInput,
  MeetingDetail,
  MeetingList,
  MeetingQuery,
  MeetingUpdateInput,
  ParticipantWithCount,
  Summary,
  Transcript,
} from "./types";

export function meetingSearchParams(query: MeetingQuery): URLSearchParams {
  const params = new URLSearchParams({ limit: "100" });
  if (query.q?.trim()) params.set("q", query.q.trim());
  for (const id of query.participantIds ?? []) params.append("participant_id", String(id));
  if (query.dateFrom) params.set("date_from", query.dateFrom);
  if (query.dateTo) params.set("date_to", query.dateTo);
  if (query.keyword) params.set("keyword", query.keyword);
  if (query.sort) params.set("sort", query.sort);
  return params;
}

const json = (body: unknown) => JSON.stringify(body);

export const api = {
  listMeetings: (query: MeetingQuery) =>
    apiFetch<MeetingList>(`/api/meetings?${meetingSearchParams(query)}`),
  getMeeting: (id: number) => apiFetch<MeetingDetail>(`/api/meetings/${id}`),
  createMeeting: (input: MeetingCreateInput) =>
    apiFetch<MeetingDetail>("/api/meetings", { method: "POST", body: json(input) }),
  updateMeeting: (id: number, input: MeetingUpdateInput) =>
    apiFetch<MeetingDetail>(`/api/meetings/${id}`, { method: "PATCH", body: json(input) }),
  deleteMeeting: (id: number) => apiFetch<void>(`/api/meetings/${id}`, { method: "DELETE" }),
  getTranscript: (id: number) => apiFetch<Transcript>(`/api/meetings/${id}/transcript`),
  getSummary: (id: number) => apiFetch<Summary>(`/api/meetings/${id}/summary`),
  regenerateSummary: (id: number) =>
    apiFetch<{ processing_status: string }>(`/api/meetings/${id}/summary/regenerate`, {
      method: "POST",
    }),
  listActionItems: (meetingId: number) =>
    apiFetch<ActionItem[]>(`/api/meetings/${meetingId}/action-items`),
  createActionItem: (meetingId: number, input: ActionItemInput) =>
    apiFetch<ActionItem>(`/api/meetings/${meetingId}/action-items`, {
      method: "POST",
      body: json(input),
    }),
  updateActionItem: (id: number, input: ActionItemInput) =>
    apiFetch<ActionItem>(`/api/action-items/${id}`, { method: "PATCH", body: json(input) }),
  deleteActionItem: (id: number) => apiFetch<void>(`/api/action-items/${id}`, { method: "DELETE" }),
  listParticipants: () => apiFetch<ParticipantWithCount[]>("/api/participants"),
};
