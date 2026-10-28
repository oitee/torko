import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  SPEAKER_NOT_IDENTIFIED,
  formatNumber,
  scriptLang,
} from "../../assets/js/format.js";
import Chip from "../../components/Chip.jsx";
import Popover from "../../components/Popover.jsx";
import TLDR from "../../components/TLDR.jsx";
import "./DebateTranscript.css";

export function countText(n, one, many) {
  return n === 1 ? `1 ${one}` : `${formatNumber(n)} ${many}`;
}

// Helper to format turn speaker display
export function getSpeakerDetails(turn) {
  if (turn.kind === "presiding" || turn.role_kind === "presiding") {
    return { name: "The Chair", isChair: true };
  }
  if (turn.kind === "crowd" || turn.role_kind === "crowd") {
    return { name: "Several members", isCrowd: true };
  }
  if (turn.attributed && turn.member) {
    return {
      name: turn.member,
      id: turn.member_id,
      party: turn.party,
      seat: turn.seat,
    };
  }
  return { name: SPEAKER_NOT_IDENTIFIED, isUnidentified: true };
}

// Helper to split turn text into paragraphs at blank lines
export function splitParagraphs(text) {
  if (!text) return [];
  return text
    .split(/\n\s*\n/)
    .map((p) => p.trim())
    .filter(Boolean);
}

export default function DebateTranscript({
  speeches = [],
  turns = [],
  people = [],
  tags = [],
  activeTagSlug = null,
  activeMemberId = null,
  onFilterChange,
}) {
  const [expandedTurns, setExpandedTurns] = useState({});
  const [unfoldedRanges, setUnfoldedRanges] = useState({});
  const [activeSpeechSeq, setActiveSpeechSeq] = useState(null);
  const [phoneSheetOpen, setPhoneSheetOpen] = useState(false);
  const [cardExpandedPhone, setCardExpandedPhone] = useState({});
  const jumpButtonRef = useRef(null);
  const sectionRef = useRef(null);
  const filterBarRef = useRef(null);

  // The rail and the speech card stick below the filter bar, so the section holds the bar's height.
  useEffect(() => {
    const bar = filterBarRef.current;
    const section = sectionRef.current;
    if (!bar || !section || typeof ResizeObserver === "undefined") return undefined;
    const observer = new ResizeObserver(() => {
      section.style.setProperty("--filter-bar-height", `${bar.offsetHeight}px`);
    });
    observer.observe(bar);
    return () => observer.disconnect();
  }, []);

  // Map speech id to speech object
  const speechMap = {};
  speeches.forEach((s, idx) => {
    speechMap[s.id] = { ...s, speechIndex: idx + 1 };
  });

  // Active filter info
  const activeTag = tags.find((t) => t.slug === activeTagSlug) || null;
  const activeMember = people.find((p) => String(p.id) === String(activeMemberId)) || null;

  // Track active speech when scrolling
  useEffect(() => {
    const handleScroll = () => {
      const speechElements = document.querySelectorAll("[data-speech-id]");
      if (speechElements.length === 0) return;

      const triggerLine = window.innerHeight * 0.35;
      let currentId = null;

      speechElements.forEach((el) => {
        const rect = el.getBoundingClientRect();
        if (rect.top <= triggerLine) {
          currentId = el.getAttribute("data-speech-id");
        }
      });

      if (currentId) {
        setActiveSpeechSeq(currentId);
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, [speeches, turns]);

  // Jump to a speech
  const jumpToSpeech = (speechId) => {
    const el = document.getElementById(`speech-${speechId}`);
    if (el) {
      const yOffset = -80;
      const y = el.getBoundingClientRect().top + window.scrollY + yOffset;
      window.scrollTo({ top: y, behavior: "smooth" });
      setActiveSpeechSeq(String(speechId));
      setPhoneSheetOpen(false);
    }
  };

  const toggleTurnExpanded = (turnSeq) => {
    setExpandedTurns((prev) => ({
      ...prev,
      [turnSeq]: !prev[turnSeq],
    }));
  };

  const toggleUnfoldRange = (rangeKey) => {
    setUnfoldedRanges((prev) => ({
      ...prev,
      [rangeKey]: !prev[rangeKey],
    }));
  };

  const togglePhoneCard = (speechId) => {
    setCardExpandedPhone((prev) => ({
      ...prev,
      [speechId]: !prev[speechId],
    }));
  };

  // Determine visibility of each turn based on filters
  // A turn is "matched" if it satisfies filter.
  // With tag filter: turns belonging to speeches with the tag are shown.
  // With member filter: turns spoken by that member (own speech or interruption) are shown.
  const isTurnMatched = (t) => {
    if (!activeTag && !activeMember) return true;
    if (activeTag) {
      if (!t.speech && !t.inside_speech) return false;
      const spId = t.speech || t.inside_speech;
      const sp = speechMap[spId];
      return sp ? (sp.tags || []).some((tag) => tag.slug === activeTag.slug) : false;
    }
    if (activeMember) {
      return String(t.member_id) === String(activeMember.id);
    }
    return true;
  };

  // Group turns into contiguous visible and folded blocks
  const blocks = [];
  let i = 0;
  while (i < turns.length) {
    const matched = isTurnMatched(turns[i]);
    let j = i;
    while (j < turns.length && isTurnMatched(turns[j]) === matched) {
      j++;
    }
    const run = turns.slice(i, j);
    const rangeKey = `${turns[i].seq}-${turns[j - 1].seq}`;

    if (!matched) {
      blocks.push({
        type: "folded",
        rangeKey,
        turns: run,
        count: run.length,
        isUnfolded: Boolean(unfoldedRanges[rangeKey]),
      });
    } else {
      // Group matched turns by speech (or between turns)
      let k = 0;
      while (k < run.length) {
        const curTurn = run[k];
        const spId = curTurn.speech || curTurn.inside_speech;
        let l = k;
        while (
          l < run.length &&
          (run[l].speech || run[l].inside_speech) === spId
        ) {
          l++;
        }
        const speechGroupTurns = run.slice(k, l);
        blocks.push({
          type: "speech_group",
          speechId: spId,
          speech: spId ? speechMap[spId] : null,
          turns: speechGroupTurns,
        });
        k = l;
      }
    }
    i = j;
  }

  // Filter sentence text
  let filterSentence =
    speeches.length === 0
      ? `This debate has no speech. It has ${turns.length} ${
          turns.length === 1 ? "turn" : "turns"
        }.`
      : `Showing the whole debate in order: ${countText(
          speeches.length,
          "speech",
          "speeches"
        )}, ${countText(people.length, "member", "members")} identified.`;
  if (activeTag) {
    const count = activeTag.speeches;
    const spWord = count === 1 ? "1 speech" : `${count} speeches`;
    filterSentence = `Showing ${spWord} tagged ${activeTag.name}. Interruptions inside them are muted.`;
  } else if (activeMember) {
    const memSp = speeches.filter((s) => String(s.member_id) === String(activeMember.id)).length;
    const memInt = turns.filter(
      (t) => String(t.member_id) === String(activeMember.id) && t.role_in_debate === "interruption"
    ).length;
    const spWord = memSp === 1 ? "1 speech" : `${memSp} speeches`;
    const intWord = memInt === 1 ? "1 interruption" : `${memInt} interruptions`;
    filterSentence = `Showing everything ${activeMember.name} said: ${spWord} and ${intWord}.`;
  }

  // Count shown
  const shownSpeechesCount = speeches.filter((s) => {
    if (activeTag) {
      return (s.tags || []).some((t) => t.slug === activeTag.slug);
    }
    if (activeMember) {
      return String(s.member_id) === String(activeMember.id);
    }
    return true;
  }).length;

  const visCountText =
    activeTag || activeMember
      ? `${shownSpeechesCount} of ${countText(speeches.length, "speech", "speeches")} shown`
      : speeches.length === 0
      ? `${formatNumber(turns.length)} turns`
      : `${countText(speeches.length, "speech", "speeches")} · ${countText(
          people.length,
          "member",
          "members"
        )} identified`;

  return (
    <section
      id="debate"
      ref={sectionRef}
      className="debate-transcript"
      aria-labelledby="debate-heading"
    >
      <div className="debate-transcript__header">
        <div className="debate-transcript__header-top">
          <h2 id="debate-heading" className="debate-transcript__title">
            The debate
          </h2>
          <span className="debate-transcript__meta mono">
            {speeches.length === 0
              ? `${formatNumber(turns.length)} turns · in the order of the record`
              : `${countText(speeches.length, "speech", "speeches")} · ${countText(
                  people.length,
                  "member",
                  "members"
                )} identified · in the order of the record`}
          </span>
        </div>

        {/* Filter bar */}
        <div ref={filterBarRef} className="debate-transcript__filter-bar" role="status">
          <div className="debate-transcript__filter-status">
            <p className="debate-transcript__filter-sentence">{filterSentence}</p>
            {activeTag && (
              <button
                type="button"
                className="debate-transcript__filter-tag-pill"
                onClick={() => onFilterChange && onFilterChange({ tag: null, member: activeMemberId })}
                aria-label={`Remove tag filter ${activeTag.name}`}
              >
                Tag: {activeTag.name} <span aria-hidden="true">✕</span>
              </button>
            )}
            {activeMember && (
              <button
                type="button"
                className="debate-transcript__filter-tag-pill"
                onClick={() => onFilterChange && onFilterChange({ tag: activeTagSlug, member: null })}
                aria-label={`Remove member filter ${activeMember.name}`}
              >
                Member: {activeMember.name} <span aria-hidden="true">✕</span>
              </button>
            )}
          </div>

          <div className="debate-transcript__filter-controls">
            {tags.length > 0 && (
            <label className="debate-transcript__filter-label">
              Tag
              <select
                className="debate-transcript__select"
                value={activeTagSlug || ""}
                onChange={(e) =>
                  onFilterChange &&
                  onFilterChange({ tag: e.target.value || null, member: activeMemberId })
                }
              >
                <option value="">All tags</option>
                {tags.map((t) => (
                  <option key={t.slug} value={t.slug}>
                    {t.name} · {t.speeches}
                  </option>
                ))}
              </select>
            </label>
            )}

            {people.length > 0 && (
            <label className="debate-transcript__filter-label">
              Member
              <select
                className="debate-transcript__select"
                value={activeMemberId || ""}
                onChange={(e) =>
                  onFilterChange &&
                  onFilterChange({ tag: activeTagSlug, member: e.target.value || null })
                }
              >
                <option value="">All members</option>
                {people.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name} · {p.party || ""}
                  </option>
                ))}
              </select>
            </label>
            )}

            <span className="debate-transcript__vis-count mono">{visCountText}</span>
          </div>
        </div>

        {/* Phone Jump to speech button */}
        {speeches.length > 0 && (
          <div className="debate-transcript__phone-jump">
            <div ref={jumpButtonRef} className="debate-transcript__jump-wrap">
              <button
                type="button"
                className="debate-transcript__jump-btn"
                onClick={() => setPhoneSheetOpen(!phoneSheetOpen)}
                aria-haspopup="dialog"
              >
                <span>Jump to speech</span>
                <span className="mono">
                  {activeSpeechSeq
                    ? `${String(activeSpeechSeq).padStart(2, "0")} / ${speeches.length}`
                    : `${speeches.length}`}
                </span>
              </button>

              <Popover
                open={phoneSheetOpen}
                onClose={() => setPhoneSheetOpen(false)}
                triggerRef={jumpButtonRef}
                className="debate-transcript__jump-popover"
                role="dialog"
                aria-label="Jump to speech"
              >
                <div className="debate-transcript__jump-sheet">
                  <div className="debate-transcript__jump-sheet-header">
                    <span className="debate-transcript__jump-sheet-title">
                      Jump to speech
                    </span>
                    <button
                      type="button"
                      className="debate-transcript__jump-close"
                      onClick={() => setPhoneSheetOpen(false)}
                      aria-label="Close"
                    >
                      ✕
                    </button>
                  </div>
                  <ol className="debate-transcript__jump-list">
                    {speeches.map((sp, idx) => (
                      <li key={sp.id}>
                        <button
                          type="button"
                          className="debate-transcript__rail-btn"
                          onClick={() => jumpToSpeech(sp.id)}
                        >
                          <span className="debate-transcript__rail-ord mono">
                            {String(idx + 1).padStart(2, "0")}
                          </span>
                          <div className="debate-transcript__rail-text">
                            <span className="debate-transcript__rail-name">
                              {sp.member || SPEAKER_NOT_IDENTIFIED}
                            </span>
                            <span className="debate-transcript__rail-meta meta">
                              {sp.party ? `${sp.party} · ` : ""}
                              <span className="mono">{formatNumber(sp.words)} words</span>
                            </span>
                          </div>
                        </button>
                      </li>
                    ))}
                  </ol>
                </div>
              </Popover>
            </div>
          </div>
        )}
      </div>

      {/* Main transcript columns */}
      <div className="debate-transcript__columns">
        {/* Left column: Sticky rail of speeches (desktop only) */}
        {speeches.length > 0 && (
          <nav
            aria-label="Speeches in this debate"
            className="debate-transcript__rail"
          >
            <div className="debate-transcript__rail-header">
              <span className="debate-transcript__rail-title">Speeches</span>
              <span className="debate-transcript__rail-total mono">
                {speeches.length}
              </span>
            </div>
            <p className="debate-transcript__rail-note meta">
              {activeTag
                ? `■ marks the ${activeTag.speeches} speeches tagged ${activeTag.name}.`
                : activeMember
                ? `■ marks the speeches by ${activeMember.name}.`
                : "Pick a speech to go to it."}
            </p>
            <ol className="debate-transcript__rail-list">
              {speeches.map((sp, idx) => {
                const isCur = String(sp.id) === String(activeSpeechSeq);
                const matchesFilter =
                  (activeTag && (sp.tags || []).some((t) => t.slug === activeTag.slug)) ||
                  (activeMember && String(sp.member_id) === String(activeMember.id));

                return (
                  <li key={sp.id}>
                    <button
                      type="button"
                      className={`debate-transcript__rail-btn ${
                        isCur ? "debate-transcript__rail-btn--active" : ""
                      }`}
                      aria-current={isCur ? "true" : undefined}
                      onClick={() => jumpToSpeech(sp.id)}
                    >
                      <span className="debate-transcript__rail-ord mono">
                        {String(idx + 1).padStart(2, "0")}
                      </span>
                      <div className="debate-transcript__rail-text">
                        <span className="debate-transcript__rail-name">
                          {sp.member || SPEAKER_NOT_IDENTIFIED}
                        </span>
                        <span className="debate-transcript__rail-meta meta">
                          {sp.party || ""} ·{" "}
                          <span className="mono">{formatNumber(sp.words)}</span>
                        </span>
                      </div>
                      <span className="debate-transcript__rail-mark mono">
                        {(activeTag || activeMember) && matchesFilter ? "■" : ""}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ol>
          </nav>
        )}

        {/* Middle and Right: Flow of blocks */}
        <div className="debate-transcript__flow">
          {blocks.map((block, bIdx) => {
            if (block.type === "folded") {
              if (block.isUnfolded) {
                return (
                  <div key={bIdx} className="debate-transcript__folded-box">
                    <button
                      type="button"
                      className="debate-transcript__fold-bar debate-transcript__fold-bar--opened"
                      onClick={() => toggleUnfoldRange(block.rangeKey)}
                      aria-expanded="true"
                    >
                      <span className="mono">···</span>
                      <span>Opened. These turns are outside the filter.</span>
                      <span className="debate-transcript__fold-action">Hide</span>
                    </button>
                    {block.turns.map((t) => (
                      <TurnItem
                        key={t.seq}
                        turn={t}
                        muted={true}
                        expanded={Boolean(expandedTurns[t.seq])}
                        onToggle={() => toggleTurnExpanded(t.seq)}
                      />
                    ))}
                  </div>
                );
              }

              return (
                <div key={bIdx} className="debate-transcript__folded-box">
                  <button
                    type="button"
                    className="debate-transcript__fold-bar"
                    onClick={() => toggleUnfoldRange(block.rangeKey)}
                    aria-expanded="false"
                    aria-label={`Show ${block.count} hidden turns`}
                  >
                    <span className="mono">···</span>
                    <span className="mono">{block.count} turns hidden</span>
                    <span className="debate-transcript__fold-action">Show</span>
                  </button>
                </div>
              );
            }

            // Speech group or between block
            const sp = block.speech;
            const isSpeech = Boolean(sp);

            return (
              <div
                key={bIdx}
                id={sp ? `speech-${sp.id}` : undefined}
                data-speech-id={sp ? sp.id : undefined}
                className={`debate-transcript__speech-row ${
                  isSpeech ? "debate-transcript__speech-row--bracket" : ""
                }`}
              >
                {/* Mobile Speech Card (accordion on phones) */}
                {isSpeech && (
                  <div className="debate-transcript__phone-card-wrap">
                    <button
                      type="button"
                      className="debate-transcript__phone-card-toggle"
                      onClick={() => togglePhoneCard(sp.id)}
                      aria-expanded={Boolean(cardExpandedPhone[sp.id])}
                    >
                      <span>
                        Speech {sp.speechIndex} of {speeches.length}
                      </span>
                      <span aria-hidden="true">·</span>
                      <span className="mono">{formatNumber(sp.words)} words</span>
                      {sp.summary && (
                        <>
                          <span aria-hidden="true">·</span>
                          <span>TLDR</span>
                        </>
                      )}
                      <span className="debate-transcript__caret">
                        {cardExpandedPhone[sp.id] ? "▴" : "▾"}
                      </span>
                    </button>

                    {cardExpandedPhone[sp.id] && (
                      <div className="debate-transcript__phone-card-content">
                        <SpeechCard
                          speech={sp}
                          totalSpeeches={speeches.length}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Turns Column */}
                <div className="debate-transcript__turns-col">
                  {block.turns.map((turn) => {
                    const isIntr = turn.role_in_debate === "interruption";
                    const isMuted =
                      (activeTag || activeMember) &&
                      (!activeMember || String(turn.member_id) !== String(activeMember.id)) &&
                      isIntr;

                    return (
                      <TurnItem
                        key={turn.seq}
                        turn={turn}
                        muted={isMuted}
                        expanded={Boolean(expandedTurns[turn.seq])}
                        onToggle={() => toggleTurnExpanded(turn.seq)}
                      />
                    );
                  })}
                </div>

                {/* Right Column: Speech Card (desktop sticky) */}
                {isSpeech && (
                  <div className="debate-transcript__card-col">
                    <SpeechCard speech={sp} totalSpeeches={speeches.length} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

// Single Turn component
function TurnItem({ turn, muted = false, expanded = false, onToggle }) {
  const details = getSpeakerDetails(turn);
  const paragraphs = splitParagraphs(turn.text);
  const isInterruption = turn.role_in_debate === "interruption";
  const hasMore = paragraphs.length > 2;
  const visibleParas = expanded || !hasMore ? paragraphs : paragraphs.slice(0, 2);

  let headerSpeaker = null;
  if (details.id) {
    headerSpeaker = (
      <Link
        to={`/member/${details.id}`}
        className="debate-transcript__speaker-link"
      >
        {details.name}
      </Link>
    );
  } else {
    headerSpeaker = (
      <span
        className={`debate-transcript__speaker-name${
          details.isUnidentified ? " debate-transcript__speaker-name--unidentified" : ""
        }`}
      >
        {details.name}
      </span>
    );
  }

  const metaParts = [];
  if (isInterruption) {
    metaParts.push("Interruption");
  }
  if (details.party) metaParts.push(details.party);
  if (details.seat) metaParts.push(details.seat);
  const metaText = metaParts.join(" · ");

  return (
    <div
      className={`debate-transcript__turn ${
        isInterruption ? "debate-transcript__turn--interruption" : ""
      } ${muted ? "debate-transcript__turn--muted" : ""}`}
    >
      <div className="debate-transcript__turn-header">
        {headerSpeaker}
        {metaText && (
          <span className="debate-transcript__turn-meta meta">
            {" "}· {metaText}
          </span>
        )}
      </div>

      <div className="debate-transcript__turn-body">
        {visibleParas.map((p, idx) => (
          <p
            key={idx}
            className="debate-transcript__para"
            lang={scriptLang(p)}
          >
            {p}
          </p>
        ))}

        {hasMore && !expanded && (
          <button
            type="button"
            className="debate-transcript__read-more"
            onClick={onToggle}
          >
            …Read more
          </button>
        )}
      </div>
    </div>
  );
}

// Speech Card component shown on the right (desktop) and accordion (phone)
function SpeechCard({ speech, totalSpeeches }) {
  const ints = speech.interruptions || 0;
  const intsText =
    ints === 0
      ? "no interruptions"
      : ints === 1
      ? "1 interruption"
      : `${formatNumber(ints)} interruptions`;

  return (
    <aside
      className="debate-speech-card"
      aria-label={`Speech by ${speech.member || SPEAKER_NOT_IDENTIFIED}`}
    >
      <div className="debate-speech-card__header">
        <span className="debate-speech-card__title">
          Speech {speech.speechIndex} of {totalSpeeches} ·{" "}
          <span className="debate-speech-card__name">
            {speech.member || SPEAKER_NOT_IDENTIFIED}
          </span>
        </span>
        <span className="debate-speech-card__stats mono meta">
          {formatNumber(speech.words)} words · {intsText}
        </span>
      </div>

      {speech.summary && (
        <div className="debate-speech-card__tldr">
          <TLDR text={speech.summary} />
        </div>
      )}

      {speech.tags && speech.tags.length > 0 && (
        <div className="debate-speech-card__chips">
          {speech.tags.map((t) => (
            <Chip key={t.slug || t.name} label={t.name} href={`/tag/${t.slug}`} />
          ))}
        </div>
      )}

      <div className="debate-speech-card__footer">
        <Link
          to={`/speech/${speech.id}`}
          className="debate-speech-card__link"
        >
          Speech page
        </Link>
      </div>
    </aside>
  );
}

export { DebateTranscript };
