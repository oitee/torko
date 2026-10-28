import React, { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import {
  SPEAKER_NOT_IDENTIFIED,
  formatDateISO,
  formatDateLong,
  formatNumber,
  termLong,
  termShort,
} from "../assets/js/format.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import Button from "../components/Button.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageAnswer from "../components/PageAnswer.jsx";
import PageLayout from "../components/PageLayout.jsx";
import Popover from "../components/Popover.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import TLDR from "../components/TLDR.jsx";
import AroundSpeech from "./speech/AroundSpeech.jsx";
import SpeechTags from "./speech/SpeechTags.jsx";
import SpeechText from "./speech/SpeechText.jsx";
import "./speech.css";

// Map speech language code to full English description.
function languageWord(lang) {
  if (lang === "en") return "Spoken in English";
  if (lang === "hi") return "Spoken in Hindi";
  if (lang === "mixed") return "Spoken in English and Hindi";
  return null;
}

// Build standard academic / policy citation for the speech.
export function formatCitation(speech) {
  if (!speech) return "";
  const speaker = speech.member || `${SPEAKER_NOT_IDENTIFIED}.`;
  const speakerPart = speech.member ? `${speech.member}.` : `${SPEAKER_NOT_IDENTIFIED}.`;
  const debate = speech.debate || "";
  const dateStr = formatDateLong(speech.date);
  const termStr = termLong(speech.term);
  const source = speech.source_url || "";
  return `${speakerPart} Speech in the Lok Sabha, ${debate}, ${dateStr}. ${termStr}. Source: ${source}`;
}

export default function Speech() {
  const { id } = useParams();
  const [speech, setSpeech] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Active marks highlighted in the speech text from "Show the words".
  const [activeMarks, setActiveMarks] = useState(null);
  const [activeTagKey, setActiveTagKey] = useState(null);

  // Citation popover state
  const [citationOpen, setCitationOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const citeButtonRef = useRef(null);

  const fetchSpeech = () => {
    setLoading(true);
    setError(null);
    getJSON(`/api/speech/${id}`)
      .then((data) => {
        setSpeech(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchSpeech();
  }, [id]);

  // Update browser tab title
  useEffect(() => {
    if (speech) {
      const speakerName = speech.member || "Speech";
      document.title = `${speakerName} · ${formatDateLong(speech.date)} · Torko`;
    } else if (error?.status === 404) {
      document.title = "Page not found · Torko";
    }
  }, [speech, error]);

  const handleToggleMarks = (marks, tagKey) => {
    if (activeMarks === marks && activeTagKey === tagKey) {
      setActiveMarks(null);
      setActiveTagKey(null);
    } else {
      setActiveMarks(marks);
      setActiveTagKey(tagKey);
    }
  };

  const handleCopyCitation = () => {
    if (!speech) return;
    const text = formatCitation(speech);
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
    }
    setCopied(true);
    setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  if (loading) {
    return (
      <main className="speech-page speech-page--loading">
        <h1 className="sr-only">Speech</h1>
        <Loading lines={4} />
      </main>
    );
  }

  if (error) {
    return (
      <main className="speech-page speech-page--error">
        <ErrorState error={error} onRetry={fetchSpeech} />
      </main>
    );
  }

  if (!speech) {
    return null;
  }

  const langText = languageWord(speech.language);

  const breadcrumbItems = [
    { label: termLong(speech.term) },
    { label: `Session ${speech.session}` },
    { label: formatDateLong(speech.date) },
    { label: speech.debate, href: `/debate/${speech.debate_id}` },
    { label: "Speech" },
  ];

  // The heading is the debate title, as sansad.in gives it. A very long title gets a smaller size, so that it fits a phone.
  const longTitle = (speech.debate || "").length > 120;

  const citationText = formatCitation(speech);

  const answerBlock = (
    <div className={`speech-header ${longTitle ? "speech-header--long-title" : ""}`}>
      <p className="speech-header__kicker">Speech in the debate</p>
      <PageAnswer>{speech.debate || "Speech"}</PageAnswer>

      <div className="speech-header__member">
        {speech.member ? (
          <>
            <Link to={`/member/${speech.member_id}`} className="speech-header__member-name">
              {speech.member}
            </Link>
            <span className="speech-header__member-meta">
              {[
                ["MP", speech.seat, speech.state].filter(Boolean).join(", "),
                speech.party ? `${speech.party} on this day` : null,
              ]
                .filter(Boolean)
                .join(" · ")}
            </span>
          </>
        ) : (
          <span className="speech-header__member-unknown">{SPEAKER_NOT_IDENTIFIED}</span>
        )}
      </div>

      <div className="speech-header__facts mono">
        <span>{formatDateISO(speech.date)}</span>
        <span>{termShort(speech.term)}</span>
        {langText && <span>{langText}</span>}
        {speech.words ? <span>{formatNumber(speech.words)} words</span> : null}
      </div>

      <div className="speech-header__actions">
        <div ref={citeButtonRef} className="speech-header__cite-wrap">
          <Button
            variant="secondary"
            onClick={() => setCitationOpen(!citationOpen)}
          >
            Cite this speech
          </Button>
          <Popover
            open={citationOpen}
            onClose={() => setCitationOpen(false)}
            triggerRef={citeButtonRef}
            className="speech-citation-popover"
            role="dialog"
            aria-label="Citation"
          >
            <div className="speech-citation">
              <p className="speech-citation__text">{citationText}</p>
              <div className="speech-citation__controls">
                <Button variant="text" onClick={handleCopyCitation}>
                  {copied ? "Citation copied" : "Copy citation"}
                </Button>
              </div>
              <p className="speech-citation__note meta">
                Cite the speech, not the TLDR. The TLDR is machine text.
              </p>
            </div>
          </Popover>
        </div>
        {speech.source_url && (
          <Button variant="text" href={speech.source_url}>
            Read the original on sansad.in
          </Button>
        )}
      </div>
    </div>
  );

  // The margin: each section has a heading over an ink rule. Counts have their number in a column of its own.
  const countRows = [
    speech.member && speech.member_counts?.term_speeches != null
      ? {
          n: speech.member_counts.term_speeches,
          text: (
            <>
              <Link to={`/member/${speech.member_id}`}>speeches</Link> by {speech.member} in the{" "}
              {termShort(speech.term)}
            </>
          ),
        }
      : null,
    speech.debate_speeches
      ? { n: speech.debate_speeches, text: `speeches in this debate. This is speech ${formatNumber(speech.earlier_speeches + 1)}.` }
      : null,
    speech.interruptions > 0
      ? { n: speech.interruptions, text: speech.interruptions === 1 ? "interruption inside this speech" : "interruptions inside this speech" }
      : null,
  ].filter(Boolean);

  const marginBlock = (
    <div className="speech-margin">
      <section className="speech-margin__section">
        <h2 className="speech-margin__heading">Counts</h2>
        <dl className="speech-margin__counts">
          {countRows.map((row, i) => (
            <div key={i} className="speech-margin__count-row">
              <dt className="speech-margin__count-n">{formatNumber(row.n)}</dt>
              <dd className="speech-margin__count-text">{row.text}</dd>
            </div>
          ))}
        </dl>
        <HowTorkoCounts>
          A speech is one range of the record that belongs to one member, from
          their first words to their last. A short remark by another member or by
          the chair inside it is an interruption. It is not part of the speech.
          The TLDR is machine text. Cite the speech, not the TLDR.
        </HowTorkoCounts>
      </section>

      <section className="speech-margin__section">
        <h2 className="speech-margin__heading">Source</h2>
        <dl className="speech-margin__source">
          <dt>Record</dt>
          <dd>Lok Sabha Debates, {formatDateLong(speech.date)}</dd>
          <dt>Debate</dt>
          <dd>{speech.debate}</dd>
          {speech.source_url && (
            <>
              <dt>Link</dt>
              <dd>
                <a href={speech.source_url}>sansad.in</a>
              </dd>
            </>
          )}
        </dl>
      </section>
    </div>
  );

  return (
    <PageLayout
      breadcrumb={<Breadcrumb items={breadcrumbItems} />}
      answer={answerBlock}
      margin={marginBlock}
    >
      <div className="speech-main">
        {speech.summary && <TLDR text={speech.summary} />}

        {speech.tags && speech.tags.length > 0 && (
          <SpeechTags
            tags={speech.tags}
            speechId={speech.id}
            activeMarks={activeMarks}
            activeTagKey={activeTagKey}
            onToggleMarks={handleToggleMarks}
          />
        )}

        <SpeechText
          turns={speech.turn_list || []}
          hasMember={Boolean(speech.member)}
          activeMarks={activeMarks}
          speaker={speech}
        />

        <AroundSpeech
          before={speech.before || []}
          after={speech.after || []}
          debateId={speech.debate_id}
          current={(speech.turn_list || []).find((t) => t.own) || null}
        />
      </div>
    </PageLayout>
  );
}
