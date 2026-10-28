import React, { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { formatDateLong } from "../assets/js/format.js";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import DebateDiscussed from "./debate/DebateDiscussed.jsx";
import DebateGlance from "./debate/DebateGlance.jsx";
import DebateHead from "./debate/DebateHead.jsx";
import DebateMethodSource from "./debate/DebateMethodSource.jsx";
import DebateSameDay from "./debate/DebateSameDay.jsx";
import DebateTranscript from "./debate/DebateTranscript.jsx";
import DebateWho from "./debate/DebateWho.jsx";
import "./debate.css";

export default function Debate() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const [debate, setDebate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const activeTagSlug = searchParams.get("tag") || null;
  const activeMemberId = searchParams.get("member") || null;

  const fetchDebate = () => {
    setLoading(true);
    setError(null);
    getJSON(`/api/debate/${id}`)
      .then((data) => {
        setDebate(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDebate();
  }, [id]);

  // Set browser tab title: "<title cut to 60 characters> · <formatDateLong(date)> · Torko"
  useEffect(() => {
    if (debate) {
      const rawTitle = debate.title || "Debate";
      const cutTitle = rawTitle.length > 60 ? rawTitle.slice(0, 60) : rawTitle;
      const dateStr = debate.date ? formatDateLong(debate.date) : "";
      document.title = `${cutTitle} · ${dateStr} · Torko`;
    } else if (error?.status === 404) {
      document.title = "Page not found · Torko";
    }
  }, [debate, error]);

  const handleFilterChange = ({ tag, member }) => {
    const next = new URLSearchParams(searchParams);
    if (tag) {
      next.set("tag", tag);
    } else {
      next.delete("tag");
    }
    if (member) {
      next.set("member", String(member));
    } else {
      next.delete("member");
    }
    setSearchParams(next, { replace: true });
  };

  const handleTagClick = (slug) => {
    const nextTag = activeTagSlug === slug ? null : slug;
    handleFilterChange({ tag: nextTag, member: null });
    if (nextTag) {
      setTimeout(() => {
        const el = document.getElementById("debate");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 50);
    }
  };

  const handleMemberClick = (memberId) => {
    const nextMember = String(activeMemberId) === String(memberId) ? null : memberId;
    handleFilterChange({ tag: null, member: nextMember });
    if (nextMember) {
      setTimeout(() => {
        const el = document.getElementById("debate");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 50);
    }
  };

  if (loading) {
    return (
      <main className="debate-page debate-page--loading">
        <h1 className="sr-only">Debate</h1>
        <Loading lines={6} />
      </main>
    );
  }

  if (error) {
    return (
      <main className="debate-page debate-page--error">
        <ErrorState error={error} onRetry={fetchDebate} />
      </main>
    );
  }

  if (!debate) {
    return null;
  }

  const hasDiscussed = debate.tags && debate.tags.length > 0;
  const hasWho =
    (debate.people && debate.people.length > 0) ||
    (debate.unidentified && debate.unidentified.speeches > 0) ||
    (debate.silent && debate.silent.length > 0);

  return (
    <div className="debate-page">
      <PageLayout
        answer={<DebateHead debate={debate} />}
      >
        <div className="debate-main">
          <DebateGlance debate={debate} />

          {(hasDiscussed || hasWho) && (
            <div className="debate-two-col">
              {hasDiscussed && (
                <DebateDiscussed
                  tags={debate.tags}
                  speechesCount={(debate.speeches || []).length}
                  selectedTagSlug={activeTagSlug}
                  onSelectTag={handleTagClick}
                />
              )}
              {hasWho && (
                <DebateWho
                  people={debate.people}
                  unidentified={debate.unidentified}
                  silent={debate.silent}
                  selectedMemberId={activeMemberId}
                  onSelectMember={handleMemberClick}
                />
              )}
            </div>
          )}

          <DebateTranscript
            speeches={debate.speeches || []}
            turns={debate.turn_list || []}
            people={debate.people || []}
            tags={debate.tags || []}
            activeTagSlug={activeTagSlug}
            activeMemberId={activeMemberId}
            onFilterChange={handleFilterChange}
          />

          <div className="debate-bottom-grid">
            <DebateSameDay sameDay={debate.same_day} date={debate.date} />
            <DebateMethodSource
              term={debate.term}
              session_label={debate.session_label}
              date={debate.date}
              source_url={debate.source_url}
            />
          </div>
        </div>
      </PageLayout>
    </div>
  );
}
