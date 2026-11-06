import { useEffect, useRef, useState } from "react";

// Follow the width of an element in CSS pixels.
// A chart that uses this width as its drawing width keeps its text at its real size on every screen.
// Without it, a wide chart scales down on a phone and its 12 px text becomes about 5 px.
export function useWidth(fallback) {
  const ref = useRef(null);
  const [width, setWidth] = useState(fallback);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(([entry]) => {
      const w = Math.round(entry.contentRect.width);
      if (w > 0) setWidth(w);
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}
