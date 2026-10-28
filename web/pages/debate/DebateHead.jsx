import React, { useRef, useState } from "react";
import { formatDateLong, termLong } from "../../assets/js/format.js";
import Breadcrumb from "../../components/Breadcrumb.jsx";
import Button from "../../components/Button.jsx";
import Popover from "../../components/Popover.jsx";
import "./DebateHead.css";

const WEEKDAYS = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];

const MONTHS_LONG = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export function formatDateWithWeekday(dateStr) {
  if (!dateStr) return "";
  const parts = String(dateStr).split("-");
  if (parts.length < 3) return String(dateStr);
  const year = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1;
  const day = parseInt(parts[2], 10);
  const d = new Date(Date.UTC(year, month, day));
  const weekday = WEEKDAYS[d.getUTCDay()];
  const monthName = MONTHS_LONG[month];
  return `${weekday}, ${day} ${monthName} ${year}`;
}

export function buildDebateCitation(debate) {
  if (!debate) return "";
  const dateStr = formatDateLong(debate.date);
  const termStr = termLong(debate.term);
  const sess = debate.session_label || `Session ${debate.session}`;
  const src = debate.source_url || "";
  return `Lok Sabha Debates, ${dateStr}. “${debate.title}”. ${termStr}, ${sess}. Source: ${src}`;
}

export default function DebateHead({ debate }) {
  const [citeOpen, setCiteOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const citeButtonWrapRef = useRef(null);

  if (!debate) return null;

  const breadcrumbItems = [
    { label: termLong(debate.term) },
    { label: debate.session_label || `Session ${debate.session}` },
    { label: formatDateLong(debate.date) },
  ];

  const weekdayDate = formatDateWithWeekday(debate.date);
  const citationText = buildDebateCitation(debate);

  const handleCopyCitation = () => {
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(citationText);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <section className="debate-head">
      <div className="debate-head__container">
        <Breadcrumb items={breadcrumbItems} />

        <div className="debate-head__title-group">
          <span className="debate-head__kicker mono">
            {debate.kind_label || "Debate"}
          </span>
          <h1 className="debate-head__title">{debate.title}</h1>
          <span className="debate-head__date mono">{weekdayDate}</span>
        </div>

        {debate.laid && (
          <p className="debate-head__laid meta">
            Laid on the table. The text was not read aloud.
          </p>
        )}

        <div className="debate-head__actions">
          {debate.source_url && (
            <a
              href={debate.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="button button--secondary"
            >
              Read the original on sansad.in
            </a>
          )}

          <div ref={citeButtonWrapRef} className="debate-head__cite-wrap">
            <Button
              variant="secondary"
              onClick={() => setCiteOpen(!citeOpen)}
            >
              Cite this debate
            </Button>

            <Popover
              open={citeOpen}
              onClose={() => setCiteOpen(false)}
              triggerRef={citeButtonWrapRef}
              className="debate-citation-popover"
              role="dialog"
              aria-label="Citation"
            >
              <div className="debate-citation">
                <p className="debate-citation__text">{citationText}</p>
                <div className="debate-citation__actions">
                  <Button variant="secondary" onClick={handleCopyCitation}>
                    {copied ? "Copied" : "Copy citation"}
                  </Button>
                  <span className="debate-citation__note meta">
                    Cite the record on sansad.in. Torko is the place you found
                    it.
                  </span>
                </div>
              </div>
            </Popover>
          </div>
        </div>
      </div>
    </section>
  );
}

export { DebateHead };
