import React from "react";
import Chip from "../../components/Chip.jsx";
import SearchBox from "../../components/SearchBox.jsx";
import { ErrorState, Loading } from "../../components/States.jsx";
import { formatDateLong } from "../../assets/js/format.js";
import HomeFigures from "./HomeFigures.jsx";
import HouseSeats from "./HouseSeats.jsx";
import "./HomeHero.css";

// The address that a search idea opens. It matches the links of the SearchBox suggestions:
// a place opens its page, and every other tag opens the search for its speeches.
export function ideaHref(idea) {
  if (idea.type === "place") return `/place/${idea.slug}`;
  return `/search?tag=${encodeURIComponent(idea.slug)}`;
}

// The label of a search idea. A long name that ends in a short form in brackets shows only the short form,
// so "Mahatma Gandhi National Rural Employment Guarantee Act (MNREGA)" shows as "MNREGA".
export function ideaLabel(name) {
  const m = /\(([^()]{2,12})\)$/.exec(name || "");
  return m && name.length > 24 ? m[1] : name;
}

export default function HomeHero({ corpus, corpusError, onRetryCorpus, ideas }) {
  const ideaList = Array.isArray(ideas) ? ideas : [];

  return (
    <section className="ink-band home-hero" aria-labelledby="home-title">
      <div className="home-hero__grid">
        <div className="home-hero__text">
          <h1 id="home-title" className="home-hero__title">
            Search what members said in the Lok Sabha
          </h1>
          {corpus?.first && corpus?.last && (
            <p className="home-hero__lede">
              Torko reads the Lok Sabha debates on sansad.in from{" "}
              <span className="home-hero__date">{formatDateLong(corpus.first)}</span> to{" "}
              <span className="home-hero__date">{formatDateLong(corpus.last)}</span>. It finds the member who
              spoke each turn. It tags each speech with its subjects. Each result links to the source page.
            </p>
          )}
          <div className="home-hero__search">
            <SearchBox />
          </div>
          {ideaList.length > 0 && (
            <div className="home-hero__ideas">
              <span className="home-hero__ideas-label">Try</span>
              {ideaList.map((idea) => (
                <Chip key={idea.slug} label={ideaLabel(idea.name)} href={ideaHref(idea)} />
              ))}
            </div>
          )}
        </div>
        <HouseSeats />
      </div>

      {corpus ? (
        <HomeFigures corpus={corpus} />
      ) : corpusError ? (
        <div className="home-hero__state">
          <ErrorState error={corpusError} onRetry={onRetryCorpus} />
        </div>
      ) : (
        <div className="home-hero__state">
          <Loading lines={2} />
        </div>
      )}
    </section>
  );
}

export { HomeHero };
