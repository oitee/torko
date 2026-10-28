import React, { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import FilterBar from "../components/FilterBar.jsx";
import PageLayout from "../components/PageLayout.jsx";
import SpeechList from "../components/SpeechList.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import MemberActivity from "./member/MemberActivity.jsx";
import MemberHead from "./member/MemberHead.jsx";
import MemberLatest from "./member/MemberLatest.jsx";
import MemberMargin from "./member/MemberMargin.jsx";
import MemberPlaces from "./member/MemberPlaces.jsx";
import MemberSubjects from "./member/MemberSubjects.jsx";
import "./member.css";

export default function Member() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const [member, setMember] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [speechesData, setSpeechesData] = useState(null);
  const [speechesLoading, setSpeechesLoading] = useState(false);
  const [speechesError, setSpeechesError] = useState(null);

  // Address search parameters for speeches
  const urlFilters = {};
  for (const key of ["term", "kind", "subject", "session", "min_words"]) {
    const val = searchParams.get(key);
    if (val) {
      urlFilters[key] = val;
    }
  }
  const hideShort = searchParams.get("min_words") === "50";

  // Fetch member profile
  const fetchMember = () => {
    setLoading(true);
    setError(null);
    getJSON(`/api/member/${id}`)
      .then((data) => {
        setMember(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchMember();
  }, [id]);

  // Update browser tab title
  useEffect(() => {
    if (member?.name) {
      document.title = `${member.name} · Torko`;
    } else if (error?.status === 404) {
      document.title = "Page not found · Torko";
    }
  }, [member, error]);

  // Fetch /api/speeches facets & counts for FilterBar and margin
  const filtersKey = JSON.stringify(urlFilters);
  useEffect(() => {
    if (!id || error) return;
    const controller = new AbortController();
    setSpeechesLoading(true);
    setSpeechesError(null);

    getJSON(
      "/api/speeches",
      { member: id, facets: 1, per_page: 1, ...urlFilters },
      { signal: controller.signal }
    )
      .then((res) => {
        setSpeechesData(res);
        setSpeechesLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) return;
        setSpeechesError(err);
        setSpeechesLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, [id, filtersKey, error]);

  const handleToggleHideShort = () => {
    const next = new URLSearchParams(searchParams);
    if (hideShort) {
      next.delete("min_words");
    } else {
      next.set("min_words", "50");
    }
    next.delete("page");
    setSearchParams(next);
  };

  // A pick on the activity chart shows that session in the list. A second pick on it shows all sessions again.
  const selectedSession = searchParams.get("session") || null;
  const handleSelectSession = (s) => {
    const value = `${s.term}-${s.session}`;
    const next = new URLSearchParams(searchParams);
    if (selectedSession === value) {
      next.delete("session");
    } else {
      next.set("session", value);
    }
    next.delete("page");
    setSearchParams(next);
    if (selectedSession !== value) {
      setTimeout(() => {
        const el = document.getElementById("speeches");
        if (el) el.scrollIntoView({ behavior: "smooth" });
      }, 50);
    }
  };

  if (loading) {
    return (
      <main className="member-page member-page--loading">
        <h1 className="sr-only">Member</h1>
        <Loading lines={4} />
      </main>
    );
  }

  if (error) {
    return (
      <main className="member-page member-page--error">
        <ErrorState error={error} onRetry={fetchMember} />
      </main>
    );
  }

  if (!member) {
    return null;
  }

  const breadcrumbItems = [
    { label: "Members" },
    ...(member.state ? [{ label: member.state }] : []),
    {
      label: member.seat_slug ? (
        <Link to={`/place/${member.seat_slug}`}>{member.seat || "Seat"}</Link>
      ) : (
        member.seat || "Member"
      ),
      href: member.seat_slug ? `/place/${member.seat_slug}` : undefined,
    },
  ];

  const speechListFilters = { member: id, ...urlFilters };

  return (
    <div className="member-page">
      <PageLayout
        breadcrumb={<Breadcrumb items={breadcrumbItems} />}
        answer={<MemberHead member={member} />}
        margin={<MemberMargin member={member} speechesData={speechesData} />}
      >
        <div className="member-main">
          {member.recent && member.recent.length > 0 && (
            <MemberLatest
              speeches={member.recent}
              totalSpeeches={member.speeches || 0}
            />
          )}

          {member.sessions && member.sessions.length > 0 && (
            <MemberActivity
              sessions={member.sessions}
              terms={member.terms || []}
              selectedSession={selectedSession}
              onSelectSession={handleSelectSession}
            />
          )}

          {member.typical && member.typical.length > 0 && (
            <MemberSubjects
              typical={member.typical}
              totalSpeeches={member.speeches || 0}
            />
          )}

          {member.places && member.places.length > 0 && (
            <MemberPlaces
              places={member.places}
              totalSpeeches={member.speeches || 0}
              seat={member.seat}
            />
          )}

          <section
            className="member-speeches"
            id="speeches"
            aria-labelledby="member-speeches-heading"
          >
            <div className="member-section-head">
              <div className="member-section-head__text">
                <h2 id="member-speeches-heading" className="member-section-title">
                  All speeches
                </h2>
              </div>
            </div>

            <div className="member-speeches__controls">
              <FilterBar
                facets={speechesData?.facets || {}}
                total={speechesData?.total ?? member.speeches}
                unfilteredTotal={member.speeches || 0}
                noun="speeches"
                groups={["term", "kind", "subject"]}
              />

              <div className="member-speeches__toggle-row">
                <label className="member-speeches__toggle-label">
                  <input
                    type="checkbox"
                    checked={hideShort}
                    onChange={handleToggleHideShort}
                    className="member-speeches__checkbox"
                  />
                  <span>Hide remarks under 50 words</span>
                </label>
              </div>
            </div>

            <SpeechList filters={speechListFilters} noun="speeches" />
          </section>
        </div>
      </PageLayout>
    </div>
  );
}
