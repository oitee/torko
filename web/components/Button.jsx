import React from "react";
import { Link } from "react-router-dom";
import "./Button.css";

// The Button component renders actions in three variants.
// It renders an anchor link when href is given. An address on another site opens in a new tab.
// Otherwise it renders a button element.
export default function Button({
  variant = "secondary",
  href,
  onClick,
  children,
  className = "",
  ...rest
}) {
  const allowedVariants = ["primary", "secondary", "text"];
  const safeVariant = allowedVariants.includes(variant) ? variant : "secondary";
  const classes = `button button--${safeVariant} ${className}`.trim();

  // An address on another site opens in a new tab, so that the reader keeps their place in Torko.
  if (href && /^https?:\/\//.test(href)) {
    return (
      <a href={href} className={classes} onClick={onClick} target="_blank" rel="noopener noreferrer">
        {children}
      </a>
    );
  }

  if (href) {
    return (
      <Link to={href} className={classes} onClick={onClick}>
        {children}
      </Link>
    );
  }

  return (
    <button type="button" className={classes} onClick={onClick} {...rest}>
      {children}
    </button>
  );
}

export { Button };
