import React, { useEffect } from "react";
import { useParams } from "react-router-dom";
import { useAnswer } from "../assets/js/useApi.js";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import NotFound from "./not_found.jsx";
import PlaceHead from "./place/PlaceHead.jsx";
import TagWhenChart from "./tag/TagWhenChart.jsx";
import PlaceHolders from "./place/PlaceHolders.jsx";
import PlaceMembers from "./place/PlaceMembers.jsx";
import PlaceParties from "./place/PlaceParties.jsx";
import PlaceSubjects from "./place/PlaceSubjects.jsx";
import PlaceSpeeches from "./place/PlaceSpeeches.jsx";
import PlaceMethod from "./place/PlaceMethod.jsx";
import "./place.css";

// The Place page shows one place (a seat, district or state) with historical trends,
// MP holders, members who spoke about it, parties, associated subjects, and speeches.
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
        <h1 className="sr-only">Place</h1>
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
          <p className="place-empty-notice">
            No speech in the record names this place yet.
          </p>
        ) : (
          <>
            <TagWhenChart years={place.years} />

            {place.holders && place.holders.length > 0 && (
              <PlaceHolders holders={place.holders} />
            )}

            <div className="place-side-by-side">
              <PlaceMembers
                members={place.members}
                totalSpeeches={place.total}
              />
              <PlaceParties
                parties={place.parties}
                placeName={place.name}
              />
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
