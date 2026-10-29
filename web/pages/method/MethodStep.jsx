import React from "react";
import "./MethodStep.css";

// MethodStep shows one step of the method: its number, a heading, a short text, and its figure.
// The figure is one line of counts. Each count states its denominator.
export default function MethodStep({ n, title, children, figure }) {
  const id = `method-step-${n}`;
  return (
    <li className="method-step" aria-labelledby={id}>
      <span className="method-step__n" aria-hidden="true">
        {n}
      </span>
      <div className="method-step__body">
        <h2 id={id} className="method-step__title">
          {title}
        </h2>
        {children}
        {figure && <p className="method-step__figure">{figure}</p>}
      </div>
    </li>
  );
}

export { MethodStep };
