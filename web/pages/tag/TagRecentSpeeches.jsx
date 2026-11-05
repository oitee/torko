import React from "react";
import SpeechGrid from "../../components/SpeechGrid.jsx";
import { termLong } from "../../assets/js/format.js";

// TagRecentSpeeches shows the recent speeches of a tag.
export default function TagRecentSpeeches({ speeches = [], slug = "", selectedTerm = "" }) {
  const termLabel = selectedTerm ? termLong(selectedTerm) : "all terms";
  return (
    <SpeechGrid
      speeches={speeches}
      meta={`latest · ${termLabel}`}
      href={`/search?tag=${slug}`}
      empty="No sample speeches for this term yet."
    />
  );
}
