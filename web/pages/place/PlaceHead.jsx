import React from "react";
import Breadcrumb from "../../components/Breadcrumb.jsx";
import { formatNumber } from "../../assets/js/format.js";

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

// Format a date string (YYYY-MM-DD) into "Month YYYY".
export function formatMonthYear(dateStr) {
  if (!dateStr) return "";
  const parts = String(dateStr).split("-");
  if (parts.length < 2) return String(dateStr);
  const year = parts[0];
  const monthIdx = parseInt(parts[1], 10) - 1;
  const month = MONTHS[monthIdx];
  return month ? `${month} ${year}` : year;
}

// Format the date range into a month-year span.
export function formatSpan(first, last) {
  const d1 = formatMonthYear(first);
  const d2 = formatMonthYear(last);
  if (d1 && d2) {
    return d1 === d2 ? d1 : `${d1} – ${d2}`;
  }
  return d1 || d2 || "–";
}

// PlaceHead renders breadcrumbs, title, description, aliases, and four big numbers.
export default function PlaceHead({ place }) {
  if (!place) return null;

  const state = place.state && place.state.name ? place.state : null;
  const breadcrumbItems = [
    ...(state ? [{ label: state.name, href: state.page ? `/place/${state.slug}` : undefined }] : []),
    { label: place.name },
  ];

  const hasAliases = Array.isArray(place.aliases) && place.aliases.length > 0;
  const hasData = (place.total || 0) > 0;

  return (
    <div className="place-head">
      <Breadcrumb items={breadcrumbItems} />

      <div className="place-head__header">
        <h1 className="head-title">{place.name}</h1>
        {place.description && (
          <p className="head-description">{place.description}</p>
        )}
        {hasAliases && (
          <span className="place-head__aliases">
            Also written: {place.aliases.join(", ")}
          </span>
        )}
      </div>

      {hasData && (
        <dl className="head-numbers">
          <div className="place-head__stat">
            <dt className="head-stat-label">
              speeches about this place
            </dt>
            <dd className="head-stat-value">{formatNumber(place.total)}</dd>
          </div>
          <div className="place-head__stat">
            <dt className="head-stat-label">debates</dt>
            <dd className="head-stat-value">{formatNumber(place.debates)}</dd>
          </div>
          <div className="place-head__stat">
            <dt className="head-stat-label">members who spoke</dt>
            <dd className="head-stat-value">{formatNumber(place.n_members)}</dd>
          </div>
          <div className="place-head__stat">
            <dt className="head-stat-label">first speech</dt>
            <dd className="head-stat-value">{formatMonthYear(place.first) || "–"}</dd>
          </div>
          <div className="place-head__stat">
            <dt className="head-stat-label">latest speech</dt>
            <dd className="head-stat-value">{formatMonthYear(place.last) || "–"}</dd>
          </div>
        </dl>
      )}
    </div>
  );
}
