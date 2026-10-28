import React from "react";
import { Link } from "react-router-dom";
import { formatDateLong, formatNumber } from "../../assets/js/format.js";
import PageAnswer from "../../components/PageAnswer.jsx";

// Build the meta line: "MP, <seat>, <state> · <current_party> since <year> · <earlier_party> <from>–<to>"
export function formatPartyPath(partyPath) {
  if (!Array.isArray(partyPath) || partyPath.length === 0) {
    return "";
  }
  // The current party is the one with to == null, or the last item in chronological order.
  const currentIndex = partyPath.findIndex((p) => p.to == null);
  const activeParty =
    currentIndex !== -1
      ? partyPath[currentIndex]
      : partyPath[partyPath.length - 1];
  const earlierParties = partyPath.filter((p) => p !== activeParty);

  const activeStr =
    activeParty.to == null
      ? `${activeParty.code} since ${activeParty.from}`
      : `${activeParty.code} ${activeParty.from}–${activeParty.to}`;

  const earlierStrs = earlierParties.map((p) =>
    p.to != null
      ? `${p.code} ${p.from}–${p.to}`
      : `${p.code} since ${p.from}`
  );

  return [activeStr, ...earlierStrs].join(" · ");
}

// Build the plain answer sentence
export function buildMemberAnswer(member) {
  const name = member?.name || "The member";
  const speechesCount = formatNumber(member?.speeches || 0);
  const termCount = Array.isArray(member?.terms) ? member.terms.length : 0;
  const termsText = termCount === 1 ? "1 term" : `${termCount} terms`;

  let sentence = `${name} has made ${speechesCount} speeches in the Lok Sabha over ${termsText}.`;

  if (Array.isArray(member?.typical) && member.typical.length > 0) {
    const top = member.typical[0];
    const topName = (top.name || "").toLowerCase();
    const lift = Number(top.lift_terms || 0).toFixed(1);
    sentence += ` The member speaks most often on ${topName}: ${lift} times the rate of the house.`;
  }

  return sentence;
}

export default function MemberHead({ member }) {
  if (!member) return null;

  const partyString = formatPartyPath(member.party_path);
  const answerText = buildMemberAnswer(member);

  const terms = member.terms || [];
  const firstDate =
    terms[0]?.first ||
    (member.recent && member.recent.length > 0
      ? member.recent[member.recent.length - 1].date
      : null);
  const lastDate =
    terms[terms.length - 1]?.last ||
    (member.recent && member.recent.length > 0
      ? member.recent[0].date
      : null);

  const statItems = [
    {
      value: String(terms.length),
      label: terms.length === 1 ? "term" : "terms",
    },
    {
      value: formatNumber(member.speeches || 0),
      label: member.speeches === 1 ? "speech" : "speeches",
    },
    firstDate
      ? {
          value: formatDateLong(firstDate),
          label: "first",
          labelFirst: true,
        }
      : null,
    lastDate
      ? {
          value: formatDateLong(lastDate),
          label: "latest",
          labelFirst: true,
        }
      : null,
  ].filter(Boolean);

  return (
    <div className="member-head">
      <div className="member-head__kicker mono">Member of the Lok Sabha</div>
      <h1 className="member-head__name">{member.name}</h1>

      <div className="member-head__line mono">
        <span>
          MP
          {member.seat && (
            <>
              ,{" "}
              {member.seat_slug ? (
                <Link to={`/place/${member.seat_slug}`} className="member-head__seat-link">
                  {member.seat}
                </Link>
              ) : (
                member.seat
              )}
            </>
          )}
          {member.state && `, ${member.state}`}
        </span>
        {partyString && <span> · {partyString}</span>}
      </div>

      <PageAnswer as="p">{answerText}</PageAnswer>

      {statItems.length > 0 && (
        <dl className="member-head__numbers" aria-label="Key counts">
          {statItems.map((item, index) => (
            <div
              key={index}
              className={`member-head__stat${item.labelFirst ? " member-head__stat--label-first" : ""}`}
            >
              <dt className="member-head__stat-label">{item.label}</dt>
              <dd className="member-head__stat-value">{item.value}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
