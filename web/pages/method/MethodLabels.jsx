import React from "react";
import { Link } from "react-router-dom";
import { formatNumber, scriptLang } from "../../assets/js/format.js";
import "./MethodLabels.css";

// MethodLabels shows the most frequent printed names of one member, with the number of turns under each.
// It shows that one member has many printed names, and that Torko joins them into one member.
// The example comes from /api/method → example.
export default function MethodLabels({ example }) {
  const labels = Array.isArray(example?.labels) ? example.labels : [];
  if (labels.length === 0) return null;

  return (
    <figure className="method-labels">
      <figcaption className="method-labels__caption">
        The {labels.length} most frequent printed names of one member:{" "}
        <Link to={`/member/${example.member_id}`}>{example.name}</Link>
      </figcaption>
      <table className="method-labels__table">
        <thead>
          <tr>
            <th scope="col">Printed name in the source</th>
            <th scope="col">Turns</th>
          </tr>
        </thead>
        <tbody>
          {labels.map((row) => (
            <tr key={row.label}>
              <td lang={scriptLang(row.label)}>{row.label}</td>
              <td>{formatNumber(row.n)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

export { MethodLabels };
