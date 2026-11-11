import { CF_ANALYTICS_TOKEN, SITE_HOST } from "./site.js";

const BEACON_SRC = "https://static.cloudflareinsights.com/beacon.min.js";

// Adds the Cloudflare Web Analytics script to the page, and returns true when it adds it.
// It adds the script only when a token is set and the page runs on the public host.
// So visits on localhost or on a test copy of the site stay out of the counts.
// Example: with host "torko.in" and token "abc", a page on torko.in gets the script. A page on localhost does not.
export function startAnalytics({ token = CF_ANALYTICS_TOKEN, host = SITE_HOST, doc = document } = {}) {
  if (!token || doc.location.hostname !== host) return false;
  const script = doc.createElement("script");
  script.defer = true;
  script.src = BEACON_SRC;
  script.setAttribute("data-cf-beacon", JSON.stringify({ token }));
  doc.body.appendChild(script);
  return true;
}
