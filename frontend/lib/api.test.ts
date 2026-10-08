import { describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch } from "./api";
import { API_URL } from "./config";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiFetch", () => {
  it("returns parsed JSON and prefixes the API base URL", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200, { status: "ok" }));
    await expect(apiFetch("/health", {}, fetchImpl)).resolves.toEqual({ status: "ok" });
    expect(fetchImpl.mock.calls[0][0]).toBe(`${API_URL}/health`);
  });

  it("sets Content-Type only when there is a body", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(200, {}));
    await apiFetch("/a", {}, fetchImpl);
    await apiFetch("/b", { method: "POST", body: "{}" }, fetchImpl);
    const headersOf = (call: number) => fetchImpl.mock.calls[call][1].headers as Headers;
    expect(headersOf(0).has("Content-Type")).toBe(false);
    expect(headersOf(1).get("Content-Type")).toBe("application/json");
  });

  it("returns undefined for 204 No Content", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    await expect(apiFetch("/x", { method: "DELETE" }, fetchImpl)).resolves.toBeUndefined();
  });

  it("turns the backend error envelope into an ApiError", async () => {
    const envelope = {
      error: { code: "meeting_not_found", message: "Meeting 4 not found", details: null },
    };
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(404, envelope));
    const error = await apiFetch("/api/meetings/4", {}, fetchImpl).catch((e: unknown) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      status: 404,
      code: "meeting_not_found",
      message: "Meeting 4 not found",
    });
  });

  it("handles non-envelope error bodies", async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response("<html>bad gateway</html>", { status: 502 }));
    await expect(apiFetch("/x", {}, fetchImpl)).rejects.toMatchObject({
      status: 502,
      code: "http_error",
    });
  });

  it("reports network failures with a friendly message", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(apiFetch("/x", {}, fetchImpl)).rejects.toMatchObject({
      status: 0,
      code: "network_error",
    });
  });
});
