import React from "react";
import Chip from "../../components/Chip.jsx";
import { formatNumber } from "../../assets/js/format.js";
import "./TagRelatedTags.css";

// The order of the related tags: the most shared speeches first. On a tie, the higher ratio to chance comes first.
export function bySharedSpeeches(a, b) {
  return (b.n ?? b.speeches_shared ?? 0) - (a.n ?? a.speeches_shared ?? 0) || (b.lift || 0) - (a.lift || 0);
}

// TagRelatedTags displays the tags that appear with the current tag more often than chance gives.
export default function TagRelatedTags({ related = [], total = null }) {
  const safeRelated = Array.isArray(related) ? related : [];

  if (safeRelated.length === 0) {
    return null;
  }

  const displayTags = [...safeRelated].sort(bySharedSpeeches).slice(0, 14);

  return (
    <section className="tag-related-tags" aria-labelledby="related-heading">
      <div className="tag-related-tags__header">
        <h2 id="related-heading" className="tag-related-tags__title">
          Related tags
        </h2>
      </div>
      <p className="tag-related-tags__note">
        Tags that appear with this tag more often than chance. The number on each tag is the speeches that carry both tags{total != null ? `, of ${formatNumber(total)} speeches with this tag` : ""}. At least 8 shared speeches. The most shared come first.
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
