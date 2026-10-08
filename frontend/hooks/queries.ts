"use client";

// Server state lives in TanStack Query: caching, loading/error states and refetching come
// from one place. Every mutation invalidates exactly the queries whose data it changes.
import { useMutation, useQuery, useQueryClient, type QueryClient } from "@tanstack/react-query";

import { api } from "@/lib/endpoints";
import type {
  ActionItemInput,
  MeetingCreateInput,
  MeetingDetail,
  MeetingQuery,
  MeetingUpdateInput,
} from "@/lib/types";

export const keys = {
  meetings: (query?: MeetingQuery) =>
    query ? (["meetings", query] as const) : (["meetings"] as const),
  meeting: (id: number) => ["meeting", id] as const,
  transcript: (id: number) => ["transcript", id] as const,
  summary: (id: number) => ["summary", id] as const,
  actionItems: (id: number) => ["action-items", id] as const,
  participants: ["participants"] as const,
  search: (q: string) => ["search", q] as const,
};

export const POLL_INTERVAL_MS = 2000;

export function isProcessing(
  meeting: Pick<MeetingDetail, "processing_status"> | undefined,
): boolean {
  return meeting?.processing_status === "pending" || meeting?.processing_status === "processing";
}

export function useMeetings(query: MeetingQuery) {
  return useQuery({ queryKey: keys.meetings(query), queryFn: () => api.listMeetings(query) });
}

/** Global search (bonus): runs once the query has 2+ characters. */
export function useGlobalSearch(q: string) {
  const query = q.trim();
  return useQuery({
    queryKey: keys.search(query),
    queryFn: () => api.search(query),
    enabled: query.length >= 2,
    staleTime: 30_000,
  });
}

export function useParticipants() {
  return useQuery({
    queryKey: keys.participants,
    queryFn: api.listParticipants,
    staleTime: 60_000,
  });
}

/** Polls every 2 s only while AI notes are being generated (eventual consistency, made visible). */
export function useMeeting(id: number) {
  return useQuery({
    queryKey: keys.meeting(id),
    queryFn: () => api.getMeeting(id),
    refetchInterval: (query) => (isProcessing(query.state.data) ? POLL_INTERVAL_MS : false),
  });
}

export function useTranscript(id: number) {
  return useQuery({ queryKey: keys.transcript(id), queryFn: () => api.getTranscript(id) });
}

export function useSummary(id: number, enabled: boolean) {
  return useQuery({
    queryKey: keys.summary(id),
    queryFn: () => api.getSummary(id),
    enabled,
    retry: false,
  });
}

export function useActionItems(id: number) {
  return useQuery({ queryKey: keys.actionItems(id), queryFn: () => api.listActionItems(id) });
}

function invalidateMeetingLists(client: QueryClient) {
  return Promise.all([
    client.invalidateQueries({ queryKey: keys.meetings() }),
    client.invalidateQueries({ queryKey: keys.participants }),
  ]);
}

export function useCreateMeeting() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: MeetingCreateInput) => api.createMeeting(input),
    onSuccess: (meeting) => {
      client.setQueryData(keys.meeting(meeting.id), meeting);
      return invalidateMeetingLists(client);
    },
  });
}

export function useUpdateMeeting(id: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: MeetingUpdateInput) => api.updateMeeting(id, input),
    onSuccess: (meeting) => {
      client.setQueryData(keys.meeting(id), meeting);
      return Promise.all([
        invalidateMeetingLists(client),
        client.invalidateQueries({ queryKey: keys.actionItems(id) }), // removed people get unassigned
      ]);
    },
  });
}

export function useDeleteMeeting() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteMeeting(id),
    onSuccess: (_data, id) => {
      for (const key of [
        keys.meeting(id),
        keys.transcript(id),
        keys.summary(id),
        keys.actionItems(id),
      ]) {
        client.removeQueries({ queryKey: key });
      }
      return invalidateMeetingLists(client);
    },
  });
}

export function useRegenerateSummary(id: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: () => api.regenerateSummary(id),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.meeting(id) }),
  });
}

function refreshCounts(client: QueryClient, meetingId: number) {
  return Promise.all([
    client.invalidateQueries({ queryKey: keys.actionItems(meetingId) }),
    client.invalidateQueries({ queryKey: keys.meeting(meetingId) }),
    client.invalidateQueries({ queryKey: keys.meetings() }),
  ]);
}

export function useCreateActionItem(meetingId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (input: ActionItemInput) => api.createActionItem(meetingId, input),
    onSuccess: () => refreshCounts(client, meetingId),
  });
}

export function useUpdateActionItem(meetingId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id: number; input: ActionItemInput }) =>
      api.updateActionItem(id, input),
    onSettled: () => refreshCounts(client, meetingId),
  });
}

export function useDeleteActionItem(meetingId: number) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteActionItem(id),
    onSuccess: () => refreshCounts(client, meetingId),
  });
}
