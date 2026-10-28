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

// SourceChip places the source glyph and hidden word before a Chip component.
// It also provides a Why button next to the chip to inspect why the tag was assigned.
export default function SourceChip({
  tag,
  onWhyClick,
  isWhyOpen = false,
}) {
  if (!tag) {
    return null;
  }

  const config = SOURCE_CONFIG[tag.source] || SOURCE_CONFIG.llm;

  return (
    <div className="source-chip">
      <span
        className="source-chip__glyph"
        aria-hidden="true"
        style={{ color: config.hue }}
      >
        {config.glyph}
      </span>
      <span className="source-chip__sr-word">{config.word}</span>
      <Chip label={tag.name} href={`/tag/${tag.slug}`} />
      {onWhyClick && (
        <button
          type="button"
          className={`source-chip__why ${isWhyOpen ? "source-chip__why--active" : ""}`}
          aria-expanded={isWhyOpen}
          aria-label={`Why is tag ${tag.name} here`}
          onClick={onWhyClick}
        >
          Why
        </button>
      )}
    </div>
  );
}

export { SourceChip };
