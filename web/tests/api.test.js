import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { clearCache, getJSON } from "../assets/js/api.js";

describe("getJSON", () => {
  beforeEach(() => {
    clearCache();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it("fetches data and returns the JSON payload", async () => {
    const payload = { id: 123, name: "Sample" };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => payload,
    });

    const data = await getJSON("/api/member/123");

    expect(data).toEqual(payload);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/member/123",
      expect.objectContaining({ signal: expect.any(AbortSignal) })
    );
  });

  it("adds query parameters and drops empty values", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    });

    await getJSON("/api/speeches", {
      term: 17,
      party: "INC",
      missing: null,
      blank: "",
      absent: undefined,
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/speeches?term=17&party=INC",
      expect.anything()
    );
  });

  it("expands list values into repeated query keys", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({}),
    });

    await getJSON("/api/speeches", { term: [16, 17] });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      "/api/speeches?term=16&term=17",
      expect.anything()
    );
  });

  it("keeps answers in memory and reuses them", async () => {
    const payload = { result: "cached" };
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => payload,
    });

    const first = await getJSON("/api/member/123");
    const second = await getJSON("/api/member/123");

    expect(first).toEqual(payload);
    expect(second).toEqual(payload);
    expect(globalThis.fetch).toHaveBeenCalledTimes(1);
  });

  it("clears the cache on clearCache", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    });

    await getJSON("/api/member/123");
    clearCache();
    await getJSON("/api/member/123");

    expect(globalThis.fetch).toHaveBeenCalledTimes(2);
  });

  it("throws not found when the server answers 404", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
    });

    await expect(getJSON("/api/member/999")).rejects.toEqual({
      status: 404,
      message: "Not found",
    });
  });

  it("throws server error on other error statuses", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });

    await expect(getJSON("/api/member/123")).rejects.toEqual({
      status: 500,
      message: "The server could not answer. Try again.",
    });
  });

  it("throws network error when fetch rejects", async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(getJSON("/api/member/123")).rejects.toEqual({
      status: 0,
      message: "Torko could not reach the server. Check the connection and try again.",
    });
  });

  it("throws timeout error after 20 seconds", async () => {
    vi.useFakeTimers();

    globalThis.fetch = vi.fn((_url, { signal }) => {
      return new Promise((_resolve, reject) => {
        signal.addEventListener("abort", () => {
          reject(new DOMException("The operation was aborted.", "AbortError"));
        });
      });
    });

    const promise = getJSON("/api/slow");

    vi.advanceTimersByTime(20000);

    await expect(promise).rejects.toEqual({
      status: 0,
      message: "The server took too long to answer. Try again.",
    });
  });

  it("throws the original abort error when the caller cancels", async () => {
    const controller = new AbortController();
    const abortReason = new Error("User changed filter");

    globalThis.fetch = vi.fn((_url, { signal }) => {
      return new Promise((_resolve, reject) => {
        signal.addEventListener("abort", () => {
          reject(controller.signal.reason);
        });
      });
    });

    const promise = getJSON("/api/speeches", {}, { signal: controller.signal });
    controller.abort(abortReason);

    await expect(promise).rejects.toBe(abortReason);
  });
});
