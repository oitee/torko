import React from "react";
import { yearRates } from "./trendsData.js";

// The numbers of the chart as a table.
export default function CompareTable({ series }) {
  const lines = series.map((s) => yearRates(s.years));
  return (
    <div className="trends-table-wrap">
      <table className="trends-table">
        <thead>
          <tr>
            <th scope="col">Year</th>
            <th scope="col">Tagged speeches</th>
            {series.map((s) => <th key={s.slug} scope="col">{s.name}</th>)}
          </tr>
        </thead>
        <tbody>
          {lines[0].map((p, j) => (
            <tr key={p.year}>
              <th scope="row">{p.year}</th>
              <td>{p.tagged}</td>
              {lines.map((l, i) => <td key={series[i].slug}>{l[j].rate === null ? "–" : `${l[j].rate.toFixed(1)}%`} · {l[j].n}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
