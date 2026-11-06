import React from "react";
import SpeechGrid from "../../components/SpeechGrid.jsx";
import { tidyTitle } from "../../assets/js/titles.js";
import { formatNumber } from "../../assets/js/format.js";

// PlaceSpeeches shows the latest speeches about a place. The Search page holds all of them, with filters.
export default function PlaceSpeeches({ speeches = [], slug = "", total = 0 }) {
  return (
    <SpeechGrid
      id="speeches"
      speeches={(Array.isArray(speeches) ? speeches : []).map((s) => ({ ...s, debate: tidyTitle(s.debate) }))}
      meta="latest · all terms"
      href={`/search?place=${slug}`}
      action={`See all ${formatNumber(total)} speeches`}
    />
  );
}
