import React, { useEffect, useRef, useState } from "react";
import { formatDateLong, formatNumber } from "../../assets/js/format.js";
import "./MethodCounts.css";

// One count. The first render always shows the full number, so a reader or a crawler without JavaScript sees it.
// After the first paint, when the row first comes into view, the count runs up from zero once.
// Without IntersectionObserver, or when the reader asks for less motion, the full number stays.
function CountUp({ n, start }) {
  const [v, setV] = useState(null);
  useEffect(() => {
    if (!start) return undefined;
    const reduced = typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) return undefined;
    const t0 = performance.now();
    let raf;
    const f = (t) => {
      const p = Math.min(1, (t - t0) / 1200);
      setV(Math.round(n * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(f);
      else setV(null);
    };
    raf = requestAnimationFrame(f);
    return () => cancelAnimationFrame(raf);
  }, [n, start]);
  return <>{formatNumber(v == null ? n : v)}</>;
}

// MethodCounts is the row of totals at the foot of the Method page. Every number comes from /api/method.
// A missing number hides its count.
export default function MethodCounts({ data }) {
  const ref = useRef(null);
  const [start, setStart] = useState(false);

  useEffect(() => {
    if (start || !ref.current || typeof IntersectionObserver === "undefined") return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setStart(true);
          observer.disconnect();
        }
      },
      { threshold: 0.3 }
    );
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [start]);

  const corpus = data?.corpus || {};
  const counts = [
    corpus.debates != null && {
      n: corpus.debates,
      label: corpus.first && corpus.last ? `debates, ${formatDateLong(corpus.first)} to ${formatDateLong(corpus.last)}` : "debates",
    },
    data?.turns?.total != null && { n: data.turns.total, label: "speaking turns" },
    data?.speeches?.total != null && { n: data.speeches.total, label: "speeches" },
    corpus.tags != null && { n: corpus.tags, label: "subject tags" },
  ].filter(Boolean);

  if (counts.length === 0) return null;

  return (
    <section ref={ref} className="method-counts" aria-label="Totals">
      {counts.map((c) => (
        <div key={c.label} className="method-counts__count">
          <b>
            <CountUp n={c.n} start={start} />
          </b>
          <span>{c.label}</span>
        </div>
      ))}
    </section>
  );
}

export { MethodCounts };
