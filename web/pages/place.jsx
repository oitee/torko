import React, { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
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
export default function Place() {
  const { slug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const [place, setPlace] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Speeches facet data for FilterBar
  const [speechesData, setSpeechesData] = useState(null);
  const [speechesLoading, setSpeechesLoading] = useState(false);
  const [speechesError, setSpeechesError] = useState(null);

  // Address search parameters for filtering speeches
  const filterParams = {};
  for (const key of ["term", "party", "kind", "session", "subject"]) {
    const val = searchParams.get(key);
    if (val) {
      filterParams[key] = val;
    }
  }
  const speechesFilters = { place: slug, ...filterParams };
  const filterKey = JSON.stringify(speechesFilters);

  // Fetch the place record from /api/place/:slug
  const fetchPlace = () => {
    setLoading(true);
    setError(null);

    getJSON(`/api/place/${slug}`)
      .then((data) => {
        setPlace(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchPlace();
  }, [slug]);

  // Update browser tab title
  useEffect(() => {
    if (place?.name) {
      document.title = `${place.name} · Torko`;
    } else if (error?.status === 404) {
      document.title = "Page not found · Torko";
    }
  }, [place, error]);

  // Fetch speeches facets when slug or filters change
  useEffect(() => {
    if (!slug) return;
    const controller = new AbortController();
    setSpeechesLoading(true);
    setSpeechesError(null);

    getJSON(
      "/api/speeches",
      { ...speechesFilters, facets: 1, per_page: 1 },
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
  }, [filterKey, slug]);

  // Session selection from When chart
  const selectedSession = searchParams.get("session") || null;
  const handleToggleSession = (s) => {
    const sessionVal = `${s.term}-${s.session}`;
    const next = new URLSearchParams(searchParams);
    if (selectedSession === sessionVal) {
      next.delete("session");
      next.delete("term");
    } else {
      next.set("term", String(s.term));
      next.set("session", sessionVal);
    }
    next.delete("page");
    setSearchParams(next);
  };

  if (loading && !place) {
    return (
      <main className="place-page place-page--loading">
        <h1 className="sr-only">Place</h1>
        <Loading lines={6} />
      </main>
    );
  }

  if (error && !place) {
    return (
      <main className="place-page place-page--error">
        <ErrorState error={error} onRetry={fetchPlace} />
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
            <PlaceWhen
              sessions={place.sessions}
              totalSpeeches={place.total}
              selectedSession={selectedSession}
              onToggleSession={handleToggleSession}
            />

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

            <PlaceSpeeches
              facets={speechesData?.facets || {}}
              total={speechesData?.total ?? place.total}
              unfilteredTotal={place.total}
              speechesFilters={speechesFilters}
            />

            <PlaceMethod />
          </>
        )}
      </div>
    </PageLayout>
  );
}
