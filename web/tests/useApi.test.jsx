import { act, renderHook, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { useApi } from "../assets/js/useApi.js";

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("useApi", () => {
  it("ignores the answer of an old key that arrives after the new answer", async () => {
    const calls = { a: deferred(), b: deferred() };
    const { result, rerender } = renderHook(({ k }) => useApi(k, () => calls[k].promise), { initialProps: { k: "a" } });

    rerender({ k: "b" });
    await act(async () => calls.b.resolve("answer b"));
    await act(async () => calls.a.resolve("answer a"));

    expect(result.current.data).toBe("answer b");
    expect(result.current.dataKey).toBe("b");
  });

  it("keeps the last answer and reports loading while the next key loads", async () => {
    const calls = { a: deferred(), b: deferred() };
    const { result, rerender } = renderHook(({ k }) => useApi(k, () => calls[k].promise), { initialProps: { k: "a" } });
    await act(async () => calls.a.resolve("answer a"));

    rerender({ k: "b" });
    expect(result.current.loading).toBe(true);
    expect(result.current.data).toBe("answer a");
  });

  it("calls nothing for a null key", () => {
    const load = vi.fn();
    const { result } = renderHook(() => useApi(null, load));
    expect(load).not.toHaveBeenCalled();
    expect(result.current.loading).toBe(false);
  });

  it("reports an error, and retry calls again", async () => {
    const load = vi.fn().mockRejectedValueOnce({ status: 500 }).mockResolvedValueOnce("answer");
    const { result } = renderHook(() => useApi("a", load));
    await waitFor(() => expect(result.current.error).toEqual({ status: 500 }));

    act(() => result.current.retry());
    await waitFor(() => expect(result.current.data).toBe("answer"));
    expect(result.current.error).toBe(null);
  });
});
