import React, { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import NotFound from "./not_found.jsx";
import PlaceHead from "./place/PlaceHead.jsx";
import PlaceWhen from "./place/PlaceWhen.jsx";
import PlaceHolders from "./place/PlaceHolders.jsx";
import PlaceMembers from "./place/PlaceMembers.jsx";
import PlaceParties from "./place/PlaceParties.jsx";
import PlaceSubjects from "./place/PlaceSubjects.jsx";
import PlaceSpeeches from "./place/PlaceSpeeches.jsx";
import PlaceMethod from "./place/PlaceMethod.jsx";
import "./place.css";

// The Place page shows one place (a seat, district or state) with historical trends,
// MP holders, members who spoke about it, parties, associated subjects, and speeches.
// The name of a place from its address while the page loads: "west-bengal" becomes "West Bengal".
export function slugTitle(slug) {
  return String(slug || "")
    .split("-")
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export default function Place() {
  const { slug } = useParams();

  const { data: place, loading, error, retry } = useAnswer(`/api/place/${slug}`);

  // Update browser tab title
  useEffect(() => {
    if (place?.name) {
      document.title = `${place.name} · Torko`;
    } else if (error?.status === 404) {
      document.title = "Page not found · Torko";
    }
  }, [place, error]);

  if (loading && !place) {
    return (
      <main className="place-page place-page--loading">
        <h1 className="head-title">{slugTitle(slug)}</h1>
        <Loading lines={6} />
      </main>
    );
  }

  if (error?.status === 404 && !place) return <NotFound />;

  if (error && !place) {
    return (
      <main className="place-page place-page--error">
        <ErrorState error={error} onRetry={retry} />
      </main>
    );
  }

  if (!place) {
    return null;
  }

  const isEmpty = (place.total || 0) === 0;

  return (
    <PageLayout
      breadcrumb={null}
      answer={<PlaceHead place={place} />}
    >
      <div className="place-main">
        {isEmpty ? (
          <>
            <p className="place-empty-notice">
              Torko has no speech with the tag {place.name}. The <Link to="/search">Search page</Link> can find speeches that
              use the name in their words.
            </p>
            {place.holders && place.holders.length > 0 && <PlaceHolders holders={place.holders} />}
          </>
        ) : (
          <>
            <PlaceWhen years={place.years} />

            {place.holders && place.holders.length > 0 && (
              <PlaceHolders holders={place.holders} />
            )}

            <div className="place-side-by-side">
              <PlaceMembers
                members={place.members}
                totalSpeeches={place.total}
              />
              <PlaceParties parties={place.parties} />
            </div>

            <PlaceSubjects
              associated={place.associated}
              related={place.related}
              placeName={place.name}
            />

            <PlaceSpeeches speeches={place.recent} slug={slug} total={place.total} />

            <PlaceMethod />
          </>
        )}
      </div>
    </PageLayout>
  );
}
