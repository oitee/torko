import React, { useState } from "react";
import { formatNumber } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";
import "./DebateDiscussed.css";

// DebateDiscussed renders the tags section of the debate.
// Allows picking a tag to filter the debate below.
// Shows at most 12 tags initially, then a "Show all N tags" expand button.
export default function DebateDiscussed({
  tags = [],
  speechesCount = 0,
  selectedTagSlug = null,
  onSelectTag,
}) {
  const [expanded, setExpanded] = useState(false);

  const topTag = tags.length > 0 ? tags[0] : null;
  const spCountText =
    speechesCount === 1 ? "1 speech" : `${formatNumber(speechesCount)} speeches`;

  const tagAnswer = topTag
    ? `${topTag.name} comes up most, in ${topTag.speeches} of ${spCountText}. Pick a tag to filter the debate below.`
    : "No tags were extracted for this debate.";

  const max = 12;
  const hasMore = tags.length > max;
  const visibleTags = expanded || !hasMore ? tags : tags.slice(0, max);

  return (
    <section id="discussed" className="debate-discussed" aria-labelledby="discussed-heading">
      <div className="debate-discussed__header">
        <h2 id="discussed-heading" className="debate-discussed__heading">
          What was discussed
        </h2>
        <p className="debate-discussed__sub">{tagAnswer}</p>
      </div>

      {tags.length > 0 && (
        <div
          role="group"
          aria-label="Tags. Pick one to filter the debate."
          className="debate-discussed__chips"
        >
          {visibleTags.map((tag) => {
            const isSelected = selectedTagSlug === tag.slug;
            return (
              <button
                key={tag.slug || tag.name}
                type="button"
                className={`chip chip--button ${
                  isSelected ? "chip--selected" : ""
                }`}
                aria-pressed={isSelected}
                onClick={() => onSelectTag && onSelectTag(isSelected ? null : tag.slug)}
              >
                {isSelected && <span className="chip__check">✓</span>}
                <span className="chip__label">{tag.name}</span>
                <span className="chip__count">{formatNumber(tag.speeches)}</span>
              </button>
            );
          })}

          {!expanded && hasMore && (
            <Button variant="text" onClick={() => setExpanded(true)}>
              Show all {tags.length} tags
            </Button>
          )}
        </div>
      )}
    </section>
  );
}

export { DebateDiscussed };
