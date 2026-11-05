import React from "react";
import Chip from "../../components/Chip.jsx";
import "./TagRelatedTags.css";

// TagRelatedTags displays the tags that appear with the current tag more often than chance gives.
// The server orders them by lift. The count on each chip is the number of shared speeches.
export default function TagRelatedTags({ related = [] }) {
  const safeRelated = Array.isArray(related) ? related : [];

  if (safeRelated.length === 0) {
    return null;
  }

  const displayTags = safeRelated.slice(0, 14);

  return (
    <section className="tag-related-tags" aria-labelledby="related-heading">
      <div className="tag-related-tags__header">
        <h2 id="related-heading" className="tag-related-tags__title">
          Related tags
        </h2>
      </div>
      <p className="tag-related-tags__note">
        Tags that appear with this tag more often than chance. At least 8 shared speeches.
      </p>

      <div className="tag-related-tags__chips">
        {displayTags.map((r) => {
          const count = r.n ?? r.speeches_shared;
          return (
            <Chip
              key={r.slug}
              label={r.name}
              count={count}
              href={`/tag/${r.slug}`}
            />
          );
        })}
      </div>
    </section>
  );
}
