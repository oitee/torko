import React, { useState } from "react";
import Button from "../../components/Button.jsx";
import Chip from "../../components/Chip.jsx";
import { CONTACT_EMAIL, SITE_URL } from "../../assets/js/site.js";
import "./SpeechTags.css";

const SHOWN = 8;
// The tags the model gave come first, then the tags of a matched word, then the tags near the summary in meaning.
const ORDER = { llm: 1, dictionary: 2, summary_tag: 3 };

// The address of an email that reports a wrong tag. It names the speech and lists its tags, so the reader can say which one.
export function reportHref(tags, speechId, pageUrl) {
  const body = `${pageUrl}\n\nThe tags of this speech: ${tags.map((t) => t.name).join(", ")}\n\nThe wrong tag, and why:\n`;
  return `mailto:${CONTACT_EMAIL}?subject=${encodeURIComponent(`Wrong tag on speech ${speechId}`)}&body=${encodeURIComponent(body)}`;
}

// SpeechTags shows the tags of a speech. Each tag links to its own page.
// It shows at most 8 tags with a "Show all N tags" button, and one link to report a wrong tag.
export default function SpeechTags({ tags, speechId }) {
  const [expanded, setExpanded] = useState(false);
  if (!tags || tags.length === 0) return null;

  const sorted = [...tags].sort((a, b) => (ORDER[a.source] || 4) - (ORDER[b.source] || 4));
  const visible = expanded ? sorted : sorted.slice(0, SHOWN);
  const pageUrl = typeof window !== "undefined" && window.location?.href ? window.location.href : `${SITE_URL}/speech/${speechId}`;

  return (
    <div className="speech-tags">
      <ul className="speech-tags__list" aria-label="Tags">
        {visible.map((tag) => (
          <li key={tag.slug || tag.name} className="speech-tags__item">
            <Chip label={tag.name} href={`/tag/${tag.slug}`} />
          </li>
        ))}
        {!expanded && sorted.length > SHOWN && (
          <li className="speech-tags__item">
            <Button variant="text" onClick={() => setExpanded(true)}>
              Show all {sorted.length} tags
            </Button>
          </li>
        )}
      </ul>
      <a href={reportHref(sorted, speechId, pageUrl)} className="speech-tags__report-link">
        Report a wrong tag
      </a>
    </div>
  );
}
