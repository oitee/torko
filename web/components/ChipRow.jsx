import React, { useState } from "react";
import Chip from "./Chip.jsx";
import Button from "./Button.jsx";
import "./ChipRow.css";

// The ChipRow component renders a list of tags as chips.
// It shows at most max chips before displaying a Show all button.
// Clicking the button reveals the remaining tags.
export default function ChipRow({ tags, max = 8 }) {
  const [expanded, setExpanded] = useState(false);

  if (!tags || tags.length === 0) {
    return null;
  }

  const hasMore = tags.length > max;
  const visibleTags = expanded || !hasMore ? tags : tags.slice(0, max);

  return (
    <ul className="chip-row">
      {visibleTags.map((tag, index) => (
        <li key={tag.slug || index} className="chip-row__item">
          <Chip label={tag.name} href={`/tag/${tag.slug}`} />
        </li>
      ))}
      {!expanded && hasMore && (
        <li className="chip-row__item">
          <Button variant="text" onClick={() => setExpanded(true)}>
            Show all {tags.length} tags
          </Button>
        </li>
      )}
    </ul>
  );
}

export { ChipRow };
