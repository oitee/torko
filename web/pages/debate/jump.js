// Scroll to one speech of the debate and put its address in the URL, so the reader can copy the link.
export function speechHash(id) {
  return `#speech-${id}`;
}

// The address bar follows the reader. The page does not reload and the history gets no new row.
export function setSpeechHash(id) {
  if (typeof window === "undefined" || !window.history?.replaceState) return;
  const { pathname, search } = window.location;
  window.history.replaceState(window.history.state, "", `${pathname}${search}${speechHash(id)}`);
}

// The id of the speech named in a URL hash such as "#speech-178368". It returns null for any other hash.
export function speechIdFromHash(hash) {
  const m = /^#speech-(\d+)$/.exec(hash || "");
  return m ? m[1] : null;
}

export function goToSpeech(id) {
  const el = document.getElementById(`speech-${id}`);
  if (!el) return false;
  const y = el.getBoundingClientRect().top + window.scrollY - 80;
  window.scrollTo({ top: y, behavior: "smooth" });
  setSpeechHash(id);
  return true;
}
