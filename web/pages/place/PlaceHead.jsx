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

// Extract state from description when it says " in <State>".
export function getStateFromDescription(description, subtype) {
  if (subtype === "state" || !description) return null;
  const match = description.match(/\bin\s+([^,.]+)/i);
  if (!match) return null;
  const raw = match[1].trim();
  if (raw.toLowerCase() === "india" || raw.toLowerCase().includes("india")) {
    return null;
  }
  return raw;
}

// Human-readable place kind label from subtype.
export function getKindLabel(subtype) {
  if (!subtype) return "Place";
  switch (subtype.toLowerCase()) {
    case "district_constituency":
      return "Seat and district";
    case "state":
      return "State";
    case "district":
      return "District";
    case "constituency":
    case "seat":
      return "Seat";
    case "city":
      return "City";
    default:
      return subtype.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
  }
}

// PlaceHead renders breadcrumbs, kicker, title, description, aliases, and four big numbers.
export default function PlaceHead({ place }) {
  if (!place) return null;

  const state = getStateFromDescription(place.description, place.subtype);
  const breadcrumbItems = [
    { label: "Places" },
    ...(state ? [{ label: state }] : []),
    { label: place.name },
  ];

  const kindLabel = getKindLabel(place.subtype);
  const span = formatSpan(place.first, place.last);
  const hasAliases = Array.isArray(place.aliases) && place.aliases.length > 0;
  const hasData = (place.total || 0) > 0;

  return (
    <div className="place-head">
      <Breadcrumb items={breadcrumbItems} />

      <div className="place-head__header">
        <span className="place-head__kicker">{kindLabel}</span>
        <h1 className="place-head__title">{place.name}</h1>
        {place.description && (
          <p className="place-head__description">{place.description}</p>
        )}
        {hasAliases && (
          <span className="place-head__aliases">
            Also written: {place.aliases.join(", ")}
          </span>
        )}
      </div>

      {hasData && (
        <dl className="place-head__numbers">
          <div className="place-head__stat">
            <dt className="place-head__stat-label">speeches about this place</dt>
            <dd className="place-head__stat-value">{formatNumber(place.total)}</dd>
          </div>
          <div className="place-head__stat">
            <dt className="place-head__stat-label">debates</dt>
            <dd className="place-head__stat-value">{formatNumber(place.debates)}</dd>
          </div>
          <div className="place-head__stat">
            <dt className="place-head__stat-label">members who spoke</dt>
            <dd className="place-head__stat-value">{formatNumber(place.n_members)}</dd>
          </div>
          <div className="place-head__stat">
            <dt className="place-head__stat-label">first and latest speech</dt>
            <dd className="place-head__stat-value">{span}</dd>
          </div>
        </dl>
      )}
    </div>
  );
}
