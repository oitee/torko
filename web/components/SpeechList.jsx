import React, { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { formatNumber } from "../assets/js/format.js";
import SpeechRow from "./SpeechRow.jsx";
import { EmptyState, ErrorState, Loading } from "./States.jsx";
import "./SpeechList.css";

// The SpeechList component renders a paged list of speeches from /api/speeches.
// The current page is tracked in the URL search parameters as ?page=N.
export default function SpeechList({ filters = {}, noun = "speeches" }) {
  const [searchParams] = useSearchParams();
  const pageParam = parseInt(searchParams.get("page") || "1", 10);
  const page = Number.isInteger(pageParam) && pageParam > 0 ? pageParam : 1;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryKey, setRetryKey] = useState(0);

  const filtersKey = JSON.stringify(filters);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getJSON(
      "/api/speeches",
      { ...filters, page, per_page: 20 },
      { signal: controller.signal }
    )
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(err);
        setLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, [filtersKey, page, retryKey]);

  if (loading) {
    return <Loading />;
  }

  if (error) {
    return (
      <ErrorState
        error={error}
        onRetry={() => setRetryKey((k) => k + 1)}
      />
    );
  }

  const speeches = data?.speeches || [];
  const total = data?.total || 0;

  if (speeches.length === 0 || total === 0) {
    return (
      <EmptyState>
        No speeches match. Remove a filter and try again.
      </EmptyState>
    );
  }

  const perPage = data?.per_page || 20;
  const start = (page - 1) * perPage + 1;
  const end = Math.min(page * perPage, total);
  const totalPages = data?.pages || Math.ceil(total / perPage) || 1;

  const nounTitle = noun.charAt(0).toUpperCase() + noun.slice(1);
  const countText = `${nounTitle} ${formatNumber(start)} to ${formatNumber(end)} of ${formatNumber(total)}`;

  const buildPageHref = (newPage) => {
    const next = new URLSearchParams(searchParams);
    if (newPage <= 1) {
      next.delete("page");
    } else {
      next.set("page", String(newPage));
    }
    const qs = next.toString();
    return qs ? `?${qs}` : "?";
  };

  return (
    <div className="speech-list">
      <div className="speech-list__count">{countText}</div>
      <div className="speech-list__items">
        {speeches.map((speech) => (
          <SpeechRow key={speech.id} speech={speech} />
        ))}
      </div>
      <nav aria-label="Pages" className="speech-list__pagination">
        {page > 1 && (
          <Link
            to={buildPageHref(page - 1)}
            className="speech-list__page-link"
          >
            ← Previous
          </Link>
        )}
        {page < totalPages && (
          <Link
            to={buildPageHref(page + 1)}
            className="speech-list__page-link"
          >
            Next →
          </Link>
        )}
      </nav>
    </div>
  );
}

export { SpeechList };
