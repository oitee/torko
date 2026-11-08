import React from "react";
import { Link } from "react-router-dom";
import SearchBox from "../../components/SearchBox.jsx";
import { dataLine, startExamples } from "./StartBlock.jsx";

// The rule that picks the suggestions. The data picks the names, so no name is a hand pick.
export const SUGGESTION_RULE =
  "The suggestions follow one rule: the 5 tags with the most speeches, a tag of two words or more as an exact phrase, and the member with the most speeches.";

// SearchLanding is the Search page before a search: a large box in the middle of the screen and a short row of suggestions.
// The latest speeches start one screen below it. busy is true while the first results of a new search load.
export default function SearchLanding({ initial = "", total, members, first, last, tagRows, topMember, busy = false, status = "" }) {
  const examples = startExamples({ tagRows, topMember });
  const line = dataLine({ total, members, first, last });
  return (
    <section className="search-landing" aria-labelledby="search-landing-title">
      <h1 id="search-landing-title" className="search-landing__title">
        Search the speeches of the Lok Sabha
      </h1>
      <div className="search-landing__box">
        <SearchBox key={initial} initial={initial} />
      </div>
      {(busy || status) && (
        <p className="search-landing__status" role="status">
          {status || "Searching…"}
        </p>
      )}
      {!busy && !status && examples.length > 0 && (
        <ul className="search-landing__suggestions" aria-label="Suggested searches" title={SUGGESTION_RULE}>
          {examples.map((e) => (
            <li key={e.key}>
              <Link to={e.to}>{e.label}</Link>
            </li>
          ))}
        </ul>
      )}
      {line && <p className="search-landing__line">{line}</p>}
      <a className="search-landing__down" href="#latest-speeches">
        Latest speeches
      </a>
    </section>
  );
}
