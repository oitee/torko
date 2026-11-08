import React from "react";
import { Link } from "react-router-dom";
import SearchBox from "../../components/SearchBox.jsx";
import { dataLine } from "./StartBlock.jsx";

// The suggested searches, picked by hand: four simple ones, and some with two or three filters that show
// what Search can do. Each one returned speeches when it was chosen.
export const SUGGESTIONS = [
  { to: "/search?tag=constitution", label: "Constitution" },
  { to: "/search?tag=railway-ministry", label: "Railway Ministry" },
  { to: "/search?tag=scheduled-tribes", label: "Scheduled Tribes" },
  { to: "/search?member=392", label: "Priya Ranjan Dasmunsi" },
  { to: "/search?q=coastal%20irrigation", label: "coastal irrigation" },
  { to: "/search?tag=farmers&term=17&party=INC", label: "Farmers, 17th Lok Sabha, INC" },
  { to: "/search?tag=railway-connectivity&state=Kerala", label: "Railway connectivity in Kerala" },
  { to: "/search?q=water%20shortage&kind=zero_hour", label: "water shortage in Zero Hour" },
];

// busy is true while the first results of a new search load.
export default function SearchLanding({ initial = "", total, members, first, last, busy = false, status = "" }) {
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
      {!busy && !status && (
        <ul className="search-landing__suggestions" aria-label="Suggested searches">
          {SUGGESTIONS.map((e) => (
            <li key={e.to}>
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
