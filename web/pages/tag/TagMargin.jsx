import React from "react";
import { Link } from "react-router-dom";
import { formatNumber } from "../../assets/js/format.js";

export default function TagMargin({ tag }) {
  if (!tag) return null;
  const slug = tag.slug;
  const by = tag.by_source || {};
  const rows = [
    { n: formatNumber(tag.total ?? 0), t: "speeches carry this tag", to: `/search?tag=${slug}` },
    tag.n_members != null ? { n: formatNumber(tag.n_members), t: "members spoke", to: `/search?tag=${slug}&view=members` } : null,
    by.llm != null ? { n: formatNumber(by.llm), t: `of ${formatNumber(tag.total ?? 0)} speeches: the model named the tag` } : null,
    by.summary_tag != null ? { n: formatNumber(by.summary_tag), t: `of ${formatNumber(tag.total ?? 0)} speeches: a word or the meaning matched` } : null,
  ].filter(Boolean);

  return (
    <div className="tag-margin">
      <section className="tag-margin__section">
        <h2 className="tag-margin__heading">Counts</h2>
        <dl className="tag-margin__counts">
          {rows.map((row) => (
            <div key={row.t} className="tag-margin__count-row">
              <dt className="tag-margin__count-n mono">{row.to ? <Link to={row.to}>{row.n}</Link> : row.n}</dt>
              <dd className="tag-margin__count-text">{row.t}</dd>
            </div>
          ))}
        </dl>
        {Array.isArray(tag.aliases) && tag.aliases.length > 0 && (
          <p className="tag-margin__text">Also called: {tag.aliases.join(", ")}.</p>
        )}
      </section>

      <section className="tag-margin__section">
        <h2 className="tag-margin__heading">Source</h2>
        <p className="tag-margin__text">
          Lok Sabha Debates, 13th to 18th Lok Sabha. Tags come from the model and from word matches.
        </p>
      </section>
    </div>
  );
}
