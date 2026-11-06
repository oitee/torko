import React from "react";
import { Link } from "react-router-dom";
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

// The name of each kind of search idea, in the plural. A kind with no name here shows its own word.
const KIND_LABELS = {
  place: "Places",
  scheme: "Schemes",
  topic: "Topics",
  law: "Laws",
  institution: "Institutions",
  person: "People",
};

// Group the search ideas by kind. A group comes in the order of its first idea in the API answer,
// and the ideas in a group keep the order of the answer.
export function groupIdeas(ideas) {
  const groups = [];
  for (const idea of Array.isArray(ideas) ? ideas : []) {
    const kind = idea.type || "other";
    let group = groups.find((g) => g.kind === kind);
    if (!group) {
      group = { kind, label: KIND_LABELS[kind] || kind.charAt(0).toUpperCase() + kind.slice(1), ideas: [] };
      groups.push(group);
    }
    group.ideas.push(idea);
  }
  return groups;
}

export default function HomeHero({ corpus, corpusError, onRetryCorpus, ideas }) {
  const groups = groupIdeas(ideas);

  return (
    <section className="ink-band home-hero" aria-labelledby="home-title">
      <div className="home-hero__grid">
        <div className="home-hero__text">
          <h1 id="home-title" className="home-hero__title">
            Search what members said in the Lok Sabha
          </h1>
          <p className="home-hero__lede">
            Torko reads the Lok Sabha debates on sansad.in
            {corpus?.first && corpus?.last && (
              <>
                {" "}
                from <span className="home-hero__date">{formatDateLong(corpus.first)}</span> to{" "}
                <span className="home-hero__date">{formatDateLong(corpus.last)}</span>
              </>
            )}
            . It finds the member who spoke each turn and tags each speech with its subjects. Each result links
            to the source page.
          </p>
          <div className="home-hero__search">
            <SearchBox />
            <Link to="/my-mp" className="home-hero__find">
              Find your MP by the name of your seat
            </Link>
          </div>
          {groups.length > 0 && (
            <div className="home-hero__ideas">
              <span className="home-hero__ideas-label">Try</span>
              {groups.map((group) => (
                <div key={group.kind} className="home-hero__group" role="group" aria-label={group.label}>
                  <span className="home-hero__group-label" aria-hidden="true">
                    {group.label}
                  </span>
                  {group.ideas.map((idea) => (
                    <Chip key={idea.slug} label={ideaLabel(idea.name)} href={ideaHref(idea)} />
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
        <HouseSeats markedHref="/my-mp" markedLabel="Find your MP: the marked seat" />
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
