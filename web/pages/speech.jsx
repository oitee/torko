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
import Count from "../components/Count.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageAnswer from "../components/PageAnswer.jsx";
import PageLayout from "../components/PageLayout.jsx";
import Popover from "../components/Popover.jsx";
import SpeakerLine from "../components/SpeakerLine.jsx";
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

  // The answer stays short, so that it fits the first screen of a phone. The debate title, which can be very long, goes under it.
  const wordsText = speech.words ? ` ${formatNumber(speech.words)} words` : "";
  const answerText = speech.member
    ? `${speech.member} spoke${wordsText} in this debate.`
    : `A speaker that Torko could not identify spoke${wordsText} in this debate.`;

  const citationText = formatCitation(speech);

  const answerBlock = (
    <div className="speech-header">
      <PageAnswer>{answerText}</PageAnswer>
      {speech.debate && (
        <p className="speech-header__debate">
          <Link to={`/debate/${speech.debate_id}`}>{speech.debate}</Link>
        </p>
      )}

      <div className="speech-header__meta">
        <SpeakerLine speech={speech} />
        <span className="speech-header__sep" aria-hidden="true">
          ·
        </span>
        <span className="mono">{formatDateISO(speech.date)}</span>
        <span className="speech-header__sep" aria-hidden="true">
          ·
        </span>
        <span className="mono">{termShort(speech.term)}</span>
        {langText && (
          <>
            <span className="speech-header__sep" aria-hidden="true">
              ·
            </span>
            <span>{langText}</span>
          </>
        )}
        <span className="speech-header__sep" aria-hidden="true">
          ·
        </span>
        <span>
          <span className="mono">{formatNumber(speech.words)}</span> words
        </span>
      </div>

      <div className="speech-header__actions">
        {speech.source_url && (
          <Button variant="text" href={speech.source_url}>
            Read the original on sansad.in
          </Button>
        )}
        <div ref={citeButtonRef} className="speech-header__cite-wrap">
          <Button
            variant="text"
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
      </div>
    </div>
  );

  const marginBlock = (
    <div className="speech-margin">
      <div className="speech-margin__counts">
        {speech.member && speech.member_counts?.term_speeches != null && (
          <div className="speech-margin__count-item">
            <Count
              n={speech.member_counts.term_speeches}
              noun={`speeches by ${speech.member} in the ${termLong(speech.term)}`}
              href={`/member/${speech.member_id}`}
            />
          </div>
        )}

        <div className="speech-margin__count-item">
          Speech <span className="mono">{speech.earlier_speeches + 1}</span> of{" "}
          <span className="mono">{formatNumber(speech.debate_speeches)}</span> in this debate
        </div>

        {speech.interruptions > 0 && (
          <div className="speech-margin__count-item">
            <span className="mono">{formatNumber(speech.interruptions)}</span>{" "}
            {speech.interruptions === 1 ? "interruption" : "interruptions"} inside this speech
          </div>
        )}
      </div>

      <HowTorkoCounts>
        A speech is one range of the record that belongs to one member, from
        their first words to their last. A short remark by another member or by
        the chair inside it is an interruption. It is not part of the speech.
        The TLDR is machine text. Cite the speech, not the TLDR.
      </HowTorkoCounts>

      <div className="speech-margin__source">
        <div className="speech-margin__source-label label">Source</div>
        <div className="speech-margin__source-date mono">
          {formatDateLong(speech.date)}
        </div>
        <div className="speech-margin__source-debate">{speech.debate}</div>
        {speech.source_url && (
          <a
            href={speech.source_url}
            className="speech-margin__source-link"
          >
            sansad.in
          </a>
        )}
      </div>
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
        />

        <AroundSpeech
          before={speech.before || []}
          after={speech.after || []}
          debateId={speech.debate_id}
        />
      </div>
    </PageLayout>
  );
}
