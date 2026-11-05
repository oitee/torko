import React, { useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { formatNumber } from "../assets/js/format.js";
import { useAnswer, useApi } from "../assets/js/useApi.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import PageLayout from "../components/PageLayout.jsx";
import SpeechGrid from "../components/SpeechGrid.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import NotFound from "./not_found.jsx";
import MemberActivity from "./member/MemberActivity.jsx";
import MemberHead from "./member/MemberHead.jsx";
import MemberMargin from "./member/MemberMargin.jsx";
import MemberPlaces from "./member/MemberPlaces.jsx";
import MemberSubjects from "./member/MemberSubjects.jsx";
import "./member.css";

export default function Member() {
  const { id } = useParams();
  const navigate = useNavigate();

  const { data: member, loading, error, retry } = useAnswer(`/api/member/${id}`);


  // Update browser tab title
  useEffect(() => {
    if (member?.name) {
      document.title = `${member.name} · Torko`;
    } else if (error?.status === 404) {
      document.title = "Page not found · Torko";
    }
  }, [member, error]);

  // The margin reads the count by debate type.
  const { data: speechesData } = useApi(id && !error ? `member-facets:${id}` : null, (signal) =>
    getJSON("/api/speeches", { member: id, facets: 1, per_page: 1 }, { signal })
  );

  // A pick on the activity chart opens the speeches of that session on the Search page.
  const handleSelectSession = (s) => navigate(`/search?member=${id}&session=${s.term}-${s.session}`);

  if (loading) {
    return (
      <main className="member-page member-page--loading">
        <h1 className="sr-only">Member</h1>
        <Loading lines={4} />
      </main>
    );
  }

  if (error?.status === 404) return <NotFound />;

  if (error) {
    return (
      <main className="member-page member-page--error">
        <ErrorState error={error} onRetry={retry} />
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


  return (
    <div className="member-page">
      <PageLayout
        breadcrumb={<Breadcrumb items={breadcrumbItems} />}
        answer={<MemberHead member={member} />}
        margin={<MemberMargin member={member} speechesData={speechesData} />}
      >
        <div className="member-main">
          <SpeechGrid
            id="speeches"
            speeches={member.recent}
            meta="latest · all terms"
            href={`/search?member=${id}`}
            action={`See all ${formatNumber(member.speeches || 0)} speeches`}
            showSpeaker={false}
          />

          {member.sessions && member.sessions.length > 0 && (
            <MemberActivity
              sessions={member.sessions}
              terms={member.terms || []}
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
        </div>
      </PageLayout>
    </div>
  );
}
