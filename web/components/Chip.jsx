import React from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../assets/js/format.js";
import "./Chip.css";

// The Chip component renders a single tag.
// It supports counts, links, selected marks, and remove buttons.
export default function Chip({
  label,
  count,
  href,
  selected = false,
  onRemove,
}) {
  const classes = [
    "chip",
    selected ? "chip--selected" : "",
    onRemove ? "chip--removable" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const innerContent = (
    <>
      {selected && <span className="chip__check">✓</span>}
      <span className="chip__label">{label}</span>
      {count !== null && count !== undefined && (
        <span className="chip__count">{formatNumber(count)}</span>
      )}
    </>
  );

  if (onRemove) {
    const LabelTag = href ? Link : "span";
    const labelProps = href
      ? { to: href, className: "chip__link" }
      : { className: "chip__content" };

    return (
      <span className={classes}>
        <LabelTag {...labelProps}>{innerContent}</LabelTag>
        <button
          type="button"
          className="chip__remove"
          aria-label={`Remove ${label}`}
          onClick={onRemove}
        >
          ✕
        </button>
      </span>
    );
  }

  if (href) {
    return (
      <Link to={href} className={classes}>
        {innerContent}
      </Link>
    );
  }

  return <span className={classes}>{innerContent}</span>;
}

export { Chip };
