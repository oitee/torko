import React, { useEffect, useRef, useState } from "react";
import { formatDateLong, termLong } from "../../assets/js/format.js";
import Breadcrumb from "../../components/Breadcrumb.jsx";
import Button from "../../components/Button.jsx";
import Popover from "../../components/Popover.jsx";
import { tidyTitle } from "../../assets/js/titles.js";
import { SITE_URL } from "../../assets/js/site.js";
import "./DebateHead.css";

const WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

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

// A date of the form 2025-12-17 as "Wednesday, 17 December 2025".
export function formatDateWithWeekday(dateStr) {
  if (!dateStr) return "";
  const parts = String(dateStr).split("-");
  if (parts.length < 3) return String(dateStr);
  const year = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10) - 1;
  const day = parseInt(parts[2], 10);
  const d = new Date(Date.UTC(year, month, day));
  return `${WEEKDAYS[d.getUTCDay()]}, ${day} ${MONTHS_LONG[month]} ${year}`;
}

// The address of the debate on Torko.
export function debateUrl(debate) {
  return `${SITE_URL}/debate/${debate.id}`;
}

// Today as 17 Dec 2025, for the "Accessed" part of the citation.
function accessedText(now) {
  const iso = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  return formatDateLong(iso);
}

// The citation of the debate: the date, the title, the term and session, the Torko address, the source, and the access date.
export function buildDebateCitation(debate, now = new Date()) {
  if (!debate) return "";
  const dateStr = formatDateLong(debate.date);
  const termStr = termLong(debate.term);
  const sess = debate.session_label || `Session ${debate.session}`;
  const torko = debate.id ? ` Torko: ${debateUrl(debate)}.` : "";
  const src = debate.source_url ? ` Source: ${debate.source_url}.` : "";
  return `Lok Sabha Debates, ${dateStr}. “${tidyTitle(debate.title)}”. ${termStr}, ${sess}.${torko}${src} Accessed ${accessedText(now)}.`;
}

export default function DebateHead({ debate }) {
  const [citeOpen, setCiteOpen] = useState(false);
  const [copyState, setCopyState] = useState("idle");
  const citeButtonWrapRef = useRef(null);
  const titleRef = useRef(null);
  const [titleOpen, setTitleOpen] = useState(false);
  const [titleCut, setTitleCut] = useState(false);

  // The title stops after 3 lines. The button shows only when the title is longer than that.
  useEffect(() => {
    const el = titleRef.current;
    if (!el || titleOpen) return undefined;
    const measure = () => setTitleCut(el.scrollHeight > el.clientHeight + 1);
    measure();
    if (typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(measure);
    observer.observe(el);
    return () => observer.disconnect();
  }, [debate?.title, titleOpen]);

  if (!debate) return null;

  const breadcrumbItems = [
    { label: termLong(debate.term) },
    { label: debate.session_label || `Session ${debate.session}` },
    { label: formatDateLong(debate.date) },
    { label: debate.kind_label || "Debate" },
  ];

  const title = tidyTitle(debate.title);
  const citationText = buildDebateCitation(debate);

  const handleCopyCitation = async () => {
    try {
      await navigator.clipboard.writeText(citationText);
      setCopyState("copied");
    } catch {
      setCopyState("failed");
    }
    setTimeout(() => setCopyState("idle"), 2000);
  };

  return (
    <section className="debate-head">
      <div className="debate-head__container">
        <Breadcrumb items={breadcrumbItems} />

        <div className="debate-head__title-group">
          <h1
            ref={titleRef}
            id="debate-title"
            className={`debate-head__title ${
              titleOpen ? "debate-head__title--open" : "debate-head__title--cut"
            }`}
          >
            {title}
          </h1>
          {(titleCut || titleOpen) && (
            <button
              type="button"
              className="button button--text debate-head__title-toggle"
              aria-controls="debate-title"
              aria-expanded={titleOpen}
              onClick={() => setTitleOpen(!titleOpen)}
            >
              {titleOpen ? "Show less of the title" : "Show full title"}
            </button>
          )}
          <p className="debate-head__date">{formatDateWithWeekday(debate.date)}</p>
        </div>

        {debate.laid && (
          <p className="debate-head__laid meta">
            Laid on the table. The text was not read aloud.
          </p>
        )}

        <div className="debate-head__actions">
          <div ref={citeButtonWrapRef} className="debate-head__cite-wrap">
            <Button
              variant="secondary"
              onClick={() => setCiteOpen(!citeOpen)}
              aria-expanded={citeOpen}
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
                  <Button variant="secondary" className="debate-citation__copy" onClick={handleCopyCitation}>
                    <span aria-live="polite">
                      {copyState === "copied" ? "Citation copied" : "Copy citation"}
                    </span>
                  </Button>
                  <span className="debate-citation__note meta" role="status">
                    {copyState === "failed"
                      ? "The copy failed. Select the text above and copy it."
                      : "Cite the official record. The Torko link helps readers find this page."}
                  </span>
                </div>
              </div>
            </Popover>
          </div>
          {debate.source_url && (
            <Button variant="text" href={debate.source_url}>
              Read the original on sansad.in
            </Button>
          )}
        </div>
      </div>
    </section>
  );
}

export { DebateHead };
