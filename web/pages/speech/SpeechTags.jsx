import React, { useState } from "react";
import { Link } from "react-router-dom";
import Button from "../../components/Button.jsx";
import { CONTACT_EMAIL, SITE_URL } from "../../assets/js/site.js";
import SourceChip, { SOURCE_CONFIG } from "./SourceChip.jsx";
import "./SpeechTags.css";

// SpeechTags renders the tag chips for the Speech page.
// Tags are ordered: first llm, then dictionary, then summary_tag.
// Shows at most 8 chips by default, with a "Show all N tags" expand button.
// Shows a source legend below chips.
// A click on "Why" opens an explanation panel with "Show the words" and a report mailto link.
export default function SpeechTags({
  tags,
  speechId,
  activeMarks,
  activeTagKey,
  onToggleMarks,
}) {
  const [expanded, setExpanded] = useState(false);
  const [openTag, setOpenTag] = useState(null);

  if (!tags || tags.length === 0) {
    return null;
  }

  // Order tags: first llm, then dictionary, then summary_tag.
  const orderWeight = { llm: 1, dictionary: 2, summary_tag: 3 };
  const sortedTags = [...tags].sort((a, b) => {
    const wa = orderWeight[a.source] || 4;
    const wb = orderWeight[b.source] || 4;
    return wa - wb;
  });

  const max = 8;
  const hasMore = sortedTags.length > max;
  const visibleTags = expanded || !hasMore ? sortedTags : sortedTags.slice(0, max);

  const handleWhyClick = (tag) => {
    if (openTag?.name === tag.name) {
      setOpenTag(null);
    } else {
      setOpenTag(tag);
    }
  };

  const getPageUrl = () => {
    if (typeof window !== "undefined" && window.location?.href) {
      return window.location.href;
    }
    return `${SITE_URL}/speech/${speechId}`;
  };

  return (
    <div className="speech-tags">
      <ul className="speech-tags__list" aria-label="Tags">
        {visibleTags.map((tag) => (
          <li key={tag.slug || tag.name} className="speech-tags__item">
            <SourceChip
              tag={tag}
              selected={openTag?.name === tag.name}
              onSelect={() => handleWhyClick(tag)}
            />
          </li>
        ))}
        {!expanded && hasMore && (
          <li className="speech-tags__item">
            <Button variant="text" onClick={() => setExpanded(true)}>
              Show all {tags.length} tags
            </Button>
          </li>
        )}
      </ul>

      <div className="speech-tags__legend meta">
        <span className="speech-tags__legend-item">
          <span
            className="speech-tags__legend-glyph"
            aria-hidden="true"
            style={{ color: SOURCE_CONFIG.llm.hue }}
          >
            {SOURCE_CONFIG.llm.glyph}
          </span>{" "}
          {SOURCE_CONFIG.llm.word}
        </span>
        <span className="speech-tags__legend-sep" aria-hidden="true">
          ·
        </span>
        <span className="speech-tags__legend-item">
          <span
            className="speech-tags__legend-glyph"
            aria-hidden="true"
            style={{ color: SOURCE_CONFIG.dictionary.hue }}
          >
            {SOURCE_CONFIG.dictionary.glyph}
          </span>{" "}
          {SOURCE_CONFIG.dictionary.word}
        </span>
        <span className="speech-tags__legend-sep" aria-hidden="true">
          ·
        </span>
        <span className="speech-tags__legend-item">
          <span
            className="speech-tags__legend-glyph"
            aria-hidden="true"
            style={{ color: SOURCE_CONFIG.summary_tag.hue }}
          >
            {SOURCE_CONFIG.summary_tag.glyph}
          </span>{" "}
          {SOURCE_CONFIG.summary_tag.word}
        </span>
        <span className="speech-tags__legend-sep" aria-hidden="true">
          ·
        </span>
        <span className="speech-tags__legend-item">Select a tag to see why it is here.</span>
      </div>

      {openTag && (
        <div className="speech-tags__why-panel" role="region" aria-label={`Why tag ${openTag.name} is here`}>
          <div className="speech-tags__why-header">
            <span
              className="speech-tags__why-glyph"
              aria-hidden="true"
              style={{
                color:
                  (SOURCE_CONFIG[openTag.source] || SOURCE_CONFIG.llm).hue,
              }}
            >
              {(SOURCE_CONFIG[openTag.source] || SOURCE_CONFIG.llm).glyph}
            </span>
            <span className="speech-tags__why-word">
              {(SOURCE_CONFIG[openTag.source] || SOURCE_CONFIG.llm).word}
            </span>
            <Link to={`/tag/${openTag.slug}`} className="speech-tags__why-tag">
              All speeches on {openTag.name}
            </Link>
          </div>

          <div className="speech-tags__why-body">
            {openTag.why && openTag.why.length > 0 ? (
              openTag.why.map((item, idx) => {
                const hasMarks = item.marks && item.marks.length > 0;
                const timesText =
                  item.marks?.length === 1
                    ? "1 time"
                    : `${item.marks?.length || 0} times`;
                const isMarkActive =
                  activeTagKey === openTag.name && activeMarks === item.marks;

                return (
                  <div key={idx} className="speech-tags__why-item">
                    {hasMarks ? (
                      <p className="speech-tags__why-sentence">
                        The words “{item.item_name || openTag.name}” appear {timesText} in this speech.{" "}
                        <button
                          type="button"
                          className="speech-tags__words-btn"
                          onClick={() =>
                            onToggleMarks && onToggleMarks(item.marks, openTag.name)
                          }
                        >
                          {isMarkActive ? "Hide the words" : "Show the words"}
                        </button>
                      </p>
                    ) : (
                      <p className="speech-tags__why-sentence">
                        {item.source === "summary_tag" || openTag.source === "summary_tag"
                          ? "The TLDR is near this tag in meaning."
                          : "The model gave this tag. The words are not in the text."}
                      </p>
                    )}

                    {item.subject && (
                      <p className="speech-tags__why-subject meta">
                        Specific subject: {item.subject}.
                      </p>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="speech-tags__why-item">
                <p className="speech-tags__why-sentence">
                  {openTag.source === "summary_tag"
                    ? "The TLDR is near this tag in meaning."
                    : "The model gave this tag. The words are not in the text."}
                </p>
              </div>
            )}
          </div>

          <div className="speech-tags__why-footer">
            <a
              href={`mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(
                `Wrong tag: ${openTag.name} (speech ${speechId})`
              )}&body=${encodeURIComponent(getPageUrl())}`}
              className="speech-tags__report-link"
            >
              Report a wrong tag
            </a>
          </div>
        </div>
      )}
    </div>
  );
}

export { SpeechTags };
