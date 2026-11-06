import React from "react";
import { formatDateLong, formatNumber } from "../../assets/js/format.js";
import HeadActions, { pageCitation } from "../../components/HeadActions.jsx";
import PageAnswer from "../../components/PageAnswer.jsx";
import { Link } from "react-router-dom";
import PartyLink from "../../components/PartyLink.jsx";

// Build the meta line: "MP, <seat>, <state> · <current_party> since <year> · <earlier_party> <from>–<to>"
export function orderedPartyPath(partyPath) {
  // The current party is the one with to == null, or the last item in chronological order.
  const currentIndex = partyPath.findIndex((p) => p.to == null);
  const activeParty =
    currentIndex !== -1
      ? partyPath[currentIndex]
      : partyPath[partyPath.length - 1];
  return [activeParty, ...partyPath.filter((p) => p !== activeParty)];
}

export function formatPct(share) {
  const pct = (Number(share) || 0) * 100;
  return pct >= 1 ? `${Math.round(pct)}%` : `${pct.toFixed(1)}%`;
}

// Tag types that only say what a speech names, not what it is about. The Home quote card uses the same rule.
const NAMING_TYPES = new Set(["institution", "place", "person", "role"]);

// The subject with the most speeches of the member. On a tie, the higher ratio to the house comes first.
// A topic, a law or a scheme comes before a tag that only names a body, a place or a person.
// So the member's own party is not "the subject" of their speeches.
export function topSubjectByCount(typical) {
  if (!Array.isArray(typical) || typical.length === 0) return null;
  const subjects = typical.filter((t) => !NAMING_TYPES.has(t.type));
  const pool = subjects.length ? subjects : typical;
  return [...pool].sort((a, b) => (b.n || 0) - (a.n || 0) || (b.lift_terms || 0) - (a.lift_terms || 0))[0];
}

// Build the plain answer sentences. Counts come first. The ratio to the house is not in the sentence.
export function buildMemberAnswer(member) {
  const name = member?.name || "The member";
  const speeches = member?.speeches || 0;
  const terms = Array.isArray(member?.terms) ? member.terms : [];
  const termsText = terms.length === 1 ? "1 term" : `${terms.length} terms`;

  let sentence = `${name} spoke ${formatNumber(speeches)} ${speeches === 1 ? "time" : "times"} in ${termsText} of the Lok Sabha.`;

  const top = topSubjectByCount(member?.typical);
  const tagged = member?.tagged_speeches;
  if (top && tagged) {
    sentence += ` Most often on ${top.name || ""}: ${formatNumber(top.n)} of ${formatNumber(tagged)} tagged speeches (${formatPct(top.member_share)}).`;
  }

  return sentence;
}

export function memberStats(member) {
  const terms = member.terms || [];
  const words = terms.reduce((sum, t) => sum + (Number(t.words) || 0), 0);
  const firstDate = terms[0]?.first || null;
  const lastDate = terms[terms.length - 1]?.last || null;
  const years = firstDate && lastDate ? `${String(firstDate).slice(0, 4)}–${String(lastDate).slice(0, 4)}` : null;
  return [
    { value: formatNumber(member.speeches || 0), label: member.speeches === 1 ? "speech" : "speeches" },
    { value: String(terms.length), label: terms.length === 1 ? "term" : "terms" },
    words > 0 ? { value: formatNumber(words), label: "words spoken" } : null,
    years ? { value: years, label: `first ${formatDateLong(firstDate)}, latest ${formatDateLong(lastDate)}` } : null,
  ].filter(Boolean);
}

export default function MemberHead({ member }) {
  if (!member) return null;

  const answerText = buildMemberAnswer(member);
  const stats = memberStats(member);
  const terms = member.terms || [];
  const firstYear = terms[0]?.first ? String(terms[0].first).slice(0, 4) : null;
  const lastYear = terms[terms.length - 1]?.last ? String(terms[terms.length - 1].last).slice(0, 4) : null;
  const citation = pageCitation({
    title: member.name,
    detail: `${formatNumber(member.speeches || 0)} speeches in the Lok Sabha${firstYear && lastYear ? `, ${firstYear} to ${lastYear}` : ""}`,
  });

  return (
    <div className="member-head">
      <h1 className="member-head__name">{member.name}</h1>

      <p className="member-head__line">
        <span className="member-head__chunk">
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
        {Array.isArray(member.party_path) &&
          member.party_path.length > 0 &&
          orderedPartyPath(member.party_path).map((p) => (
            <span className="member-head__chunk" key={`${p.code}-${p.from}`}>
              {" · "}
              <PartyLink code={p.code} />{" "}
              {p.to == null ? "since " : ""}
              {p.to == null ? p.from : `${p.from}–${p.to}`}
            </span>
          ))}
      </p>

      <PageAnswer as="p">{answerText}</PageAnswer>

      {stats.length > 0 && (
        <dl className="member-head__numbers" aria-label="Key counts">
          {stats.map((item) => (
            <div key={item.label} className="member-head__stat">
              <dt className="member-head__stat-label">{item.label}</dt>
              <dd className="member-head__stat-value">{item.value}</dd>
            </div>
          ))}
        </dl>
      )}

      <HeadActions citation={citation} />
    </div>
  );
}
