import { useEffect, useRef, useState } from "react";

// useReveal tells when an element first comes into view, so the page can fade it in once.
// Without IntersectionObserver (an old browser, or the test runner) the element counts as seen at once,
// so no content ever stays hidden.
export default function useReveal() {
  const ref = useRef(null);
  const [seen, setSeen] = useState(() => typeof window === "undefined" || !("IntersectionObserver" in window));

  useEffect(() => {
    if (seen || !ref.current) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setSeen(true);
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -10% 0px" }
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [seen]);

  return [ref, seen];
}

export { useReveal };
