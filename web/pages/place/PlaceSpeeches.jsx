import React from "react";
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
      </div>

      <div className="place-speeches__list">
        <SpeechList filters={speechesFilters} noun="speeches" />
      </div>
    </section>
  );
}
