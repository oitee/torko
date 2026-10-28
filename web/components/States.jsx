import React from "react";
import Button from "./Button.jsx";
import "./States.css";

// The Loading component shows grey bars while data loads.
// It has no animation.
// It marks aria-busy="true" and provides hidden text for screen readers.
export function Loading({ lines = 3 }) {
  const lineCount = typeof lines === "number" && lines > 0 ? lines : 3;
  const bars = Array.from({ length: lineCount });

  return (
    <div className="states-loading" aria-busy="true" role="status">
      <span className="states-loading__sr-only">Loading</span>
      {bars.map((_, index) => (
        <div key={index} className="states-loading__bar" aria-hidden="true" />
      ))}
    </div>
  );
}

// The ErrorState component shows API failure messages.
// It shows Page not found without a button for 404 status.
// Other statuses show the message and a Try again button.
export function ErrorState({ error, onRetry }) {
  if (error?.status === 404) {
    return (
      <div className="states-error" role="alert">
        <p className="states-error__message">Page not found</p>
      </div>
    );
  }

  const message = error?.message || "The server could not answer. Try again.";

  return (
    <div className="states-error" role="alert">
      <p className="states-error__message">{message}</p>
      {onRetry && (
        <Button variant="secondary" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}

// The EmptyState component shows a message when a query returns no items.
// It sets the sentence in meta colour.
export function EmptyState({ children }) {
  if (!children) {
    return null;
  }

  return (
    <div className="states-empty">
      <p className="states-empty__text">{children}</p>
    </div>
  );
}
