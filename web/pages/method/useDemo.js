import { useEffect, useRef, useState } from "react";

// useDemo runs the looping animation of one example on the Method page.
// The loop runs only while the example is on screen. It stops when the example leaves the screen.
// Without IntersectionObserver (an old browser, or the test runner), or when the reader asks for less motion,
// the demo is static: the loop never runs, and the example shows its final state.
//
// run(sleep) is one pass of the animation. sleep(ms) waits, and it rejects when the loop must stop.
// pause is the wait in milliseconds between two passes.
export default function useDemo(run, pause = 1200) {
  const ref = useRef(null);
  const [isStatic] = useState(
    () =>
      typeof window === "undefined" ||
      !("IntersectionObserver" in window) ||
      (typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches)
  );
  const [visible, setVisible] = useState(false);
  const runRef = useRef(run);
  runRef.current = run;

  useEffect(() => {
    if (isStatic || !ref.current) return undefined;
    const observer = new IntersectionObserver((entries) => setVisible(entries.some((e) => e.isIntersecting)), {
      threshold: 0.25,
    });
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, [isStatic]);

  useEffect(() => {
    if (isStatic || !visible) return undefined;
    let stopped = false;
    const timers = new Set();
    const sleep = (ms) =>
      new Promise((resolve, reject) => {
        if (stopped) return reject(STOP);
        const t = setTimeout(() => {
          timers.delete(t);
          if (stopped) reject(STOP);
          else resolve();
        }, ms);
        timers.add(t);
      });
    (async () => {
      try {
        while (!stopped) {
          await runRef.current(sleep);
          await sleep(pause);
        }
      } catch (e) {
        if (e !== STOP) throw e;
      }
    })();
    return () => {
      stopped = true;
      timers.forEach(clearTimeout);
    };
  }, [isStatic, visible, pause]);

  return [ref, isStatic];
}

const STOP = Symbol("stop");

export { useDemo };
