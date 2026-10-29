import React from "react";
import { Link } from "react-router-dom";
import Button from "../../components/Button.jsx";
import { formatNumber, ordinal } from "../../assets/js/format.js";
import "./HomeMember.css";

// A list of terms in running text (e.g. 15th, 17th and 18th Lok Sabha).
export function termList(terms) {
  const list = (Array.isArray(terms) ? terms : []).map(ordinal);
  if (list.length === 0) return "";
  const words = list.length === 1 ? list[0] : `${list.slice(0, -1).join(", ")} and ${list[list.length - 1]}`;
  return `${words} Lok Sabha`;
}

// HomeMember shows how Torko turns a printed speaker label into one member.
// The member comes from /api/home/featured → member.
export default function HomeMember({ member }) {
  if (!member) return null;

  const speeches = `${formatNumber(member.speeches)} ${member.speeches === 1 ? "speech" : "speeches"}`;
  const terms = termList(member.terms);

  return (
    <section className="home-feature" aria-labelledby="home-member-title">
      <div className="home-feature__text">
        <h3 id="home-member-title" className="home-feature__title">
          Read every speech by one member.
        </h3>
        <p className="home-feature__body">
          The record prints the name of a member in many forms. Torko matches each printed name to one member. A
          member keeps one identity in all terms.
        </p>
        <div className="home-feature__action">
          <Button variant="text" href={`/member/${member.member_id}`}>
            Read the {speeches} by {member.name}
          </Button>
        </div>
      </div>

      <div className="home-member">
        <div className="home-member__side">
          <p className="home-member__label">The record says</p>
          <p className="home-member__printed">{member.printed}</p>
        </div>
        <span className="home-member__arrow" aria-hidden="true">
          →
        </span>
        <div className="home-member__side home-member__side--found">
          <p className="home-member__label">Torko finds</p>
          <Link to={`/member/${member.member_id}`} className="home-member__name">
            {member.name}
          </Link>
          {member.seat && (
            <p className="home-member__seat">
              MP for{" "}
              {member.seat_slug ? <Link to={`/place/${member.seat_slug}`}>{member.seat}</Link> : member.seat}
              {member.state ? `, ${member.state}` : ""}
            </p>
          )}
          <p className="home-member__counts">
            {speeches}
            {terms ? ` in the ${terms}` : ""}
          </p>
        </div>
      </div>
    </section>
  );
}

export { HomeMember };
