import React, { useState } from "react";

// MethodBlock is the "How Torko counts" control of a chart. It is a real disclosure.
// On a wide screen it starts open. On a phone it starts closed.
// full is the exact text of the rules from the API. It sits in a second closed control for a reader who wants every word.
export default function MethodBlock({ children, full }) {
  const [open] = useState(() => typeof window !== "undefined" && typeof window.matchMedia === "function" && window.matchMedia("(min-width: 1024px)").matches);
  return (
    <details className="trends-method" open={open || undefined}>
      <summary className="trends-method__summary">How Torko counts</summary>
      <div className="trends-method__body">
        {children}
        {full && (
          <details className="trends-method__full">
            <summary>Exact wording of the rules</summary>
            <p>{full}</p>
          </details>
        )}
      </div>
    </details>
  );
}
