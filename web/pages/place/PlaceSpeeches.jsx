import React from "react";
import SpeechGrid from "../../components/SpeechGrid.jsx";
import { formatNumber } from "../../assets/js/format.js";

// PlaceSpeeches shows the latest speeches about a place. The Search page holds all of them, with filters.
export default function PlaceSpeeches({ speeches = [], slug = "", total = 0 }) {
  return (
    <SpeechGrid
      id="speeches"
      speeches={speeches}
      meta="latest · all terms"
      href={`/search?place=${slug}`}
      action={`See all ${formatNumber(total)} speeches`}
    />
  );
}
