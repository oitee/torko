import React from "react";
import { Link } from "react-router-dom";
import Button from "../../components/Button.jsx";
import { formatNumber } from "../../assets/js/format.js";
import { Loading } from "../../components/States.jsx";
import "./HomeMethod.css";

// The rows of the card: each is a count with its denominator, and a link to the step of the Method page.
// A row whose figures are missing in the answer is left out.
export function methodRows(method) {
  const turns = method?.turns;
  const speeches = method?.speeches;
  const oneSpeaker = turns?.total != null && turns?.chair_or_crowd != null ? turns.total - turns.chair_or_crowd : null;
  const minWords = speeches?.min_words ?? 50;

  return [
    turns?.total != null && {
      key: "read",
      href: "/method#read",
      value: formatNumber(turns.total),
      label: "turns read from the debates",
    },
    turns?.member != null &&
      oneSpeaker != null && {
        key: "who",
        href: "/method#who",
        value: formatNumber(turns.member),
        label: `of ${formatNumber(oneSpeaker)} turns of one speaker have a member name`,
      },
    speeches?.total != null && {
      key: "join",
      href: "/method#join",
      value: formatNumber(speeches.total),
      label: "speeches, joined from the turns",
    },
    speeches?.with_tag != null &&
      speeches?.eligible != null && {
        key: "subjects",
        href: "/method#subjects",
        value: formatNumber(speeches.with_tag),
        label: `of ${formatNumber(speeches.eligible)} speeches of ${minWords} words or more have a tag`,
      },
  ].filter(Boolean);
}

// HomeMethod is the last block of the Home page: the text of the link to the Method page,
// and a card with the real counts of the steps. The counts come from /api/method.
// Without the answer the block shows the text alone.
export default function HomeMethod({ method, loading }) {
  const rows = methodRows(method);

  return (
    <section className="home-feature home-feature--method" aria-labelledby="home-method-title">
      <div className="home-feature__text">
        <h3 id="home-method-title" className="home-feature__title">
          How Torko works
        </h3>
        <p className="home-feature__body">
          Read how Torko finds the member who spoke each turn and the subjects of each speech. The page also says
          what Torko gets wrong.
        </p>
        <div className="home-feature__action">
          <Button variant="text" href="/method" className="home-feature__stretch">
            Read how Torko works
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="home-method home-method--loading">
          <Loading lines={4} />
        </div>
      ) : (
        rows.length > 0 && (
          <ol className="home-method" aria-label="The steps of Torko, with their counts">
            {rows.map((row) => (
              <li key={row.key} className="home-method__row">
                <Link to={row.href} className="home-method__link">
                  <span className="home-method__value">{row.value}</span>
                  <span className="home-method__label">{row.label}</span>
                </Link>
              </li>
            ))}
          </ol>
        )
      )}
    </section>
  );
}

export { HomeMethod };
