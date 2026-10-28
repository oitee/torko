import React from "react";
import "./PageAnswer.css";

// The PageAnswer component renders the main page answer in display type.
// It limits text width to 72 characters.
// It shows an optional Count element inside the sentence.
// By default it renders an h1 element.
export default function PageAnswer({ as: Tag = "h1", children, count }) {
  if (!children && !count) {
    return null;
  }

  return (
    <Tag className="page-answer">
      {children}
      {count ? <> {count}</> : null}
    </Tag>
  );
}

export { PageAnswer };
