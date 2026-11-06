import React from "react";
import { Link } from "react-router-dom";
import { formatNumber, termLong } from "../../assets/js/format.js";

const TAG_EXAMPLES = 5;
const PHRASE_POOL = 10;

// The example searches. The rule is fixed, and the data picks the examples:
// the 5 tags with the most speeches, then the most common tag with two or more words in its name as an exact phrase,
// then the member with the most speeches.
export function startExamples({ tagRows, topMember }) {
  const tags = (tagRows || []).slice(0, TAG_EXAMPLES).map((t) => ({
    key: `tag-${t.slug}`,
    to: `/search?tag=${encodeURIComponent(t.slug)}`,
    label: t.tag,
    n: t.n,
  }));
  const phraseTag = (tagRows || []).slice(TAG_EXAMPLES, PHRASE_POOL + TAG_EXAMPLES).find((t) => t.tag.trim().split(/\s+/).length >= 2);
  const phrase = phraseTag
    ? [{ key: "phrase", to: `/search?q=${encodeURIComponent(`"${phraseTag.tag}"`)}`, label: `“${phraseTag.tag}”`, note: "exact words" }]
    : [];
  const member = topMember
    ? [{ key: "member", to: `/search?member=${topMember.id}`, label: topMember.name, note: "member" }]
    : [];
  return [...tags, ...phrase, ...member];
}

export function dataLine({ total, members, first, last }) {
  const years = first && last ? `${String(first).slice(0, 4)} to ${String(last).slice(0, 4)}` : "";
  const parts = [];
  if (total != null) parts.push(`${formatNumber(total)} speeches`);
  if (members != null) parts.push(`${parts.length ? "by " : ""}${formatNumber(members)} members`);
  const line = parts.join(" ");
  return years ? (line ? `${line}, ${years}` : years) : line;
}

export default function StartBlock({ total, members, first, last, tagRows, topMember, termRows }) {
  const line = dataLine({ total, members, first, last });
  const examples = startExamples({ tagRows, topMember });
  const terms = [...(termRows || [])].sort((a, b) => b.term - a.term);
  return (
    <section className="search-start" aria-labelledby="search-start-title">
      <h2 id="search-start-title" className="search-start__title">Start a search</h2>
      {line && <p className="search-start__line">{line}</p>}
      <p className="search-start__hint">Type words, a name, or a question. Put words in quote marks for an exact phrase.</p>
      {examples.length > 0 && (
        <div className="search-start__group">
          <h3 className="search-start__kind">Example searches</h3>
          <ul className="search-start__list">
            {examples.map((e) => (
              <li key={e.key}>
                <Link to={e.to} className="search-start__link">{e.label}</Link>
                {e.n != null && <span className="search-start__n">{formatNumber(e.n)} speeches</span>}
                {e.note && <span className="search-start__note">{e.note}</span>}
              </li>
            ))}
          </ul>
          <p className="search-start__rule">
            The examples follow one rule. They are the 5 tags with the most speeches, the first of the next 10 tags with two words or more as an exact phrase, and the member with the most speeches.
          </p>
        </div>
      )}
      {terms.length > 0 && (
        <div className="search-start__group">
          <h3 className="search-start__kind">Browse by term</h3>
          <ul className="search-start__list">
            {terms.map((t) => (
              <li key={t.term}>
                <Link to={`/search?term=${t.term}`} className="search-start__link">{termLong(t.term)}</Link>
                <span className="search-start__n">{formatNumber(t.n)} speeches</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
