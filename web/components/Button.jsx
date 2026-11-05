import React from "react";
import { Link } from "react-router-dom";
import "./Button.css";

// The Button component renders actions in three variants.
// It renders an anchor link when href is given.
// Otherwise it renders a button element.
export default function Button({
  variant = "secondary",
  href,
  onClick,
  children,
  className = "",
}) {
  const allowedVariants = ["primary", "secondary", "text"];
  const safeVariant = allowedVariants.includes(variant) ? variant : "secondary";
  const classes = `button button--${safeVariant} ${className}`.trim();

  if (href) {
    return (
      <Link to={href} className={classes} onClick={onClick}>
        {children}
      </Link>
    );
  }

  return (
    <button type="button" className={classes} onClick={onClick}>
      {children}
    </button>
  );
}

export { Button };
