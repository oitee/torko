import React from "react";
import { useSearchParams } from "react-router-dom";
import FilterBar from "../../components/FilterBar.jsx";
import SpeechList from "../../components/SpeechList.jsx";
import { formatNumber } from "../../assets/js/format.js";

const FILTER_GROUPS = ["term", "party", "kind"];

export default function PlaceSpeeches({
  facets = {},
  total,
  unfilteredTotal,
  speechesFilters = {},
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const hideShort = searchParams.get("min_words") === "50";

  const handleToggleHideShort = () => {
    const next = new URLSearchParams(searchParams);
    if (hideShort) {
      next.delete("min_words");
    } else {
      next.set("min_words", "50");
    }
    next.delete("page");
    setSearchParams(next);
  };

  const currentTotal = total !== undefined && total !== null ? total : unfilteredTotal;
  const countLabel = `${formatNumber(currentTotal)} ${
    currentTotal === 1 ? "speech" : "speeches"
  }`;

  return (
    <section
      id="speeches"
      className="place-section place-speeches"
      aria-labelledby="speeches-heading"
    >
      <div className="place-section__header">
        <h2 id="speeches-heading" className="place-section__title">
          Speeches
        </h2>
        <span className="place-speeches__count mono">{countLabel}</span>
      </div>

      <div className="place-speeches__controls">
        <FilterBar
          facets={facets}
          total={currentTotal}
          unfilteredTotal={unfilteredTotal}
          noun="speeches"
          groups={FILTER_GROUPS}
        />

        <label className="place-speeches__toggle">
          <input
            type="checkbox"
            checked={hideShort}
            onChange={handleToggleHideShort}
            className="place-speeches__checkbox"
          />
          <span>Hide remarks under 50 words</span>
        </label>
      </div>

      <div className="place-speeches__list">
        <SpeechList filters={speechesFilters} noun="speeches" />
      </div>
    </section>
  );
}
