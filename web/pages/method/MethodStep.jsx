import React from "react";
import useReveal from "./useReveal.js";
import "./MethodStep.css";

// MethodStep is one node of the flow on the Method page: a numbered node on the line that joins the steps,
// a heading, a short text, a looping example from real data, and the figure of the step.
// The figure is one line of counts. Each count states its denominator.
export default function MethodStep({ n, title, children, figure, example, last = false }) {
  const [ref, seen] = useReveal();
  const id = `method-step-${n}`;
  const classes = ["method-step", seen ? "method-step--seen" : "", last ? "method-step--last" : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <li ref={ref} className={classes} aria-labelledby={id}>
      <div className="method-step__rail" aria-hidden="true">
        <span className="method-step__n">{n}</span>
      </div>
      <div className="method-step__body">
        <h2 id={id} className="method-step__title">
          {title}
        </h2>
        {children}
        {example && <div className="method-step__example">{example}</div>}
        {figure && <p className="method-step__figure">{figure}</p>}
      </div>
    </li>
  );
}

export { MethodStep };
