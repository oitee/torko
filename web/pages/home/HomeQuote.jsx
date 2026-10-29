import React from "react";
import { Link } from "react-router-dom";
import Button from "../../components/Button.jsx";
import Chip from "../../components/Chip.jsx";
import { countOf, formatDateISO } from "../../assets/js/format.js";
import "./HomeQuote.css";

// The most chips that the quote shows.
export const MAX_QUOTE_TAGS = 3;

// The tag types that come first. A topic or a scheme tells the reader what the speech is about.
// A place, a person or an institution only says what the speech names.
const FIRST_TYPES = new Set(["topic", "scheme"]);

// The rule for the chips of the quote. The tags belong to the whole speech, not to the quoted sentence.
// 1. Take the tags of type topic or scheme, in the order of the API answer.
// 2. If fewer than MAX_QUOTE_TAGS remain, add the other tags, in the order of the API answer.
// 3. Stop at MAX_QUOTE_TAGS.
export function pickQuoteTags(tags, max = MAX_QUOTE_TAGS) {
  const list = Array.isArray(tags) ? tags : [];
  const first = list.filter((t) => FIRST_TYPES.has(t.type));
  const rest = list.filter((t) => !FIRST_TYPES.has(t.type));
  return [...first, ...rest].slice(0, max);
}

// The page of a tag. A place tag has its own page.
function tagHref(tag) {
  return tag.type === "place" ? `/place/${tag.slug}` : `/tag/${tag.slug}`;
}

// HomeQuote shows one sentence of a real speech and the tags of that speech.
// The quote comes from /api/home/featured → quote.
export default function HomeQuote({ quote }) {
  if (!quote) return null;

  const tags = Array.isArray(quote.tags) ? quote.tags : [];
  const shown = pickQuoteTags(tags);

  return (
    <section className="home-feature" aria-labelledby="home-quote-title">
      <div className="home-feature__text">
        <h3 id="home-quote-title" className="home-feature__title">
          Find speeches by subject.
        </h3>
        <p className="home-feature__body">
          Torko gives each speech the tags of its subjects. A tag finds a speech also when the speech does not use
          the words of the tag.
        </p>
        <div className="home-feature__action">
          <Button variant="text" href={`/speech/${quote.speech_id}`}>
            Read the speech
          </Button>
        </div>
      </div>

      <figure className="home-quote">
        <blockquote className="home-quote__text">“{quote.text}”</blockquote>
        <figcaption className="home-quote__source">
          <Link to={`/member/${quote.member_id}`} className="home-quote__member">
            {quote.member}
          </Link>
          <span className="home-quote__meta">
            <span className="home-quote__date">{formatDateISO(quote.date)}</span>
            {quote.debate && <> · {quote.debate}</>}
          </span>
        </figcaption>
        {shown.length > 0 && (
          <div className="home-quote__tags">
            <div className="home-quote__chips">
              {shown.map((tag) => (
                <Chip key={tag.slug} label={tag.name} href={tagHref(tag)} />
              ))}
            </div>
            <p className="home-quote__count">{countOf(shown.length, tags.length, "tags of this speech")}</p>
          </div>
        )}
      </figure>
    </section>
  );
}

export { HomeQuote };
