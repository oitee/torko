import React from "react";
import { Link } from "react-router-dom";

// The answers of /api/ask in this visit, by question. After the page changes the address to the filters,
// the Read as line takes its words from here. A shared link has no answer here, so the line uses the chips.
export const askAnswers = new Map();

// AskLine shows how Torko read a question: "Read “...” as: by Shashi Tharoor · about Kerala · on Floods".
// It names each word that did not become a filter, and links to a plain search of the whole question.
export default function AskLine({ question, chips = [] }) {
  if (!question) return null;
  const answer = askAnswers.get(question);
  const parts = answer ? answer.read_as.map((r) => r.text) : chips.map((c) => c.label);
  const words = answer ? answer.words : "";
  const dropped = answer ? answer.dropped || [] : [];
  return (
    <div className="search-ask" role="note">
      <p className="search-ask__line">
        <span className="search-ask__label">Read “{question}” as:</span>{" "}
        {parts.length > 0 ? parts.join(" · ") : "a search of the words"}
        {words && parts.length > 0 && <> · the words “{words}”</>}
      </p>
      {dropped.map((d) => (
        <p key={d.text} className="search-ask__note">
          “{d.text}” is not a filter: {d.why}.
        </p>
      ))}
      <p className="search-ask__note">
        Remove a filter below to widen the list, or{" "}
        <Link to={`/search?q=${encodeURIComponent(question)}`}>search the words of the question instead</Link>.
      </p>
    </div>
  );
}
