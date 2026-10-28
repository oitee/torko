import React from "react";
import Chip from "../../components/Chip.jsx";
import "./SourceChip.css";

// The source glyphs, words, and CSS tokens for each tag extraction source.
export const SOURCE_CONFIG = {
  llm: {
    glyph: "◆",
    word: "the model named it",
    hue: "var(--source-model)",
  },
  dictionary: {
    glyph: "“”",
    word: "a word matched",
    hue: "var(--source-word)",
  },
  summary_tag: {
    glyph: "≈",
    word: "near in meaning",
    hue: "var(--source-meaning)",
  },
};

// SourceChip is a Chip with the source glyph inside it, before the name. The glyph is hidden from screen readers.
// A visually hidden word says the source instead. A click selects the tag: the page then explains it and marks its words.
export default function SourceChip({ tag, selected = false, onSelect }) {
  if (!tag) {
    return null;
  }

  const config = SOURCE_CONFIG[tag.source] || SOURCE_CONFIG.llm;
  const prefix = (
    <>
      <span className="source-chip__glyph" aria-hidden="true" style={{ color: config.hue }}>
        {config.glyph}
      </span>
      <span className="source-chip__sr-word">{config.word}:</span>
    </>
  );

  return <Chip label={tag.name} prefix={prefix} selected={selected} onClick={onSelect} />;
}

export { SourceChip };
