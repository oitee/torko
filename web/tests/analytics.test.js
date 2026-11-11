import { describe, expect, it } from "vitest";
import { startAnalytics } from "../assets/js/analytics.js";

// A small stand-in for the page document, with a host name and a body that records the added scripts.
function fakeDoc(hostname) {
  const added = [];
  return {
    added,
    location: { hostname },
    createElement: () => ({ setAttribute(name, value) { this[name] = value; } }),
    body: { appendChild: (el) => added.push(el) },
  };
}

describe("startAnalytics", () => {
  it("adds the Cloudflare script with the token on the public host", () => {
    const doc = fakeDoc("torko.in");
    expect(startAnalytics({ token: "abc123", host: "torko.in", doc })).toBe(true);
    expect(doc.added).toHaveLength(1);
    expect(doc.added[0].src).toBe("https://static.cloudflareinsights.com/beacon.min.js");
    expect(doc.added[0].defer).toBe(true);
    expect(JSON.parse(doc.added[0]["data-cf-beacon"])).toEqual({ token: "abc123" });
  });

  it("adds nothing on localhost, so local visits stay out of the counts", () => {
    const doc = fakeDoc("localhost");
    expect(startAnalytics({ token: "abc123", host: "torko.in", doc })).toBe(false);
    expect(doc.added).toHaveLength(0);
  });

  it("adds nothing when the token is empty", () => {
    const doc = fakeDoc("torko.in");
    expect(startAnalytics({ token: "", host: "torko.in", doc })).toBe(false);
    expect(doc.added).toHaveLength(0);
  });
});
