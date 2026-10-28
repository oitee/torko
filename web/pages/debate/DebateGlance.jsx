import React from "react";
import { formatNumber } from "../../assets/js/format.js";
import "./DebateGlance.css";

// Helper to compute summary sentence and totals for At a Glance
export function buildGlanceData(debate) {
  const speeches = debate?.speeches || [];
  const people = debate?.people || [];
  const turns = debate?.turn_list || [];
  const tags = debate?.tags || [];

  if (speeches.length === 0) {
    const turnCountText = turns.length === 1 ? "1 turn" : `${turns.length} turns`;
    return {
      sentence: `This debate has no speech. It has ${turnCountText}.`,
      figures: null,
    };
  }

  const spN = speeches.length;
  const memN = people.length;
  const spCountText = spN === 1 ? "1 speech" : `${formatNumber(spN)} speeches`;
  const memCountText = memN === 1 ? "1 member" : `${formatNumber(memN)} members`;
  const hasUnidentified = (debate?.unidentified?.speeches || 0) > 0;

  // With an unidentified speaker, "by N members" would leave that speech out, so the count says what it counts.
  let sentence = hasUnidentified
    ? `${spCountText}. ${memCountText} identified.`
    : `${spCountText} by ${memCountText}.`;

  const topTag = tags.length > 0 ? tags[0] : null;
  if (topTag) {
    sentence += ` ${topTag.name} came up most, in ${topTag.speeches} of ${spCountText}.`;
  }

  const totalWords = speeches.reduce((sum, s) => sum + (s.words || 0), 0);
  const totalInterruptions = speeches.reduce((sum, s) => sum + (s.interruptions || 0), 0);

  if (totalInterruptions > 0) {
    const timesText = totalInterruptions === 1 ? "1 time" : `${formatNumber(totalInterruptions)} times`;
    sentence += ` Members and the chair broke into a speech ${timesText}.`;
  }

  const figures = [
    { n: formatNumber(spN), label: spN === 1 ? "speech" : "speeches" },
    { n: formatNumber(memN), label: memN === 1 ? "member identified" : "members identified" },
    { n: formatNumber(totalWords), label: "words in all speeches" },
    { n: formatNumber(totalInterruptions), label: "interruptions inside speeches" },
  ];

  return { sentence, figures };
}

export default function DebateGlance({ debate }) {
  if (!debate) return null;

  const { sentence, figures } = buildGlanceData(debate);

  return (
    <section id="glance" className="debate-glance" aria-labelledby="glance-heading">
      <h2 id="glance-heading" className="debate-glance__heading">
        At a glance
      </h2>
      <p className="debate-glance__sentence">{sentence}</p>

      {figures && (
        <div className="debate-glance__figures">
          {figures.map((fig, idx) => (
            <div key={idx} className="debate-glance__fig-box">
              <span className="debate-glance__fig-num mono">{fig.n}</span>
              <span className="debate-glance__fig-label">{fig.label}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export { DebateGlance };
