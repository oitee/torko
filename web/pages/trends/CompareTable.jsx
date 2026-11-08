import React from "react";
import { formatNumber } from "../../assets/js/format.js";
import { displayName, fmtShare, yearRates } from "./trendsData.js";

export default function CompareTable({ series }) {
  const lines = series.map((s) => yearRates(s.years));
  return (
    <div>
      <div className="trends-table-wrap">
        <table className="trends-table">
          <caption className="trends-table__caption">Share is the percent of the tagged speeches of the year that carry the subject. Speeches is the count of those speeches.</caption>
          <thead>
            <tr>
              <th scope="col">Year</th>
              <th scope="col">Tagged speeches</th>
              {series.map((s) => (
                <React.Fragment key={s.slug}>
                  <th scope="col">{displayName(s.name)} share</th>
                  <th scope="col">{displayName(s.name)} speeches</th>
                </React.Fragment>
              ))}
            </tr>
          </thead>
          <tbody>
            {lines[0].map((p, j) => (
              <tr key={p.year}>
                <th scope="row" className="trends-table__num">{p.year}</th>
                <td className="trends-table__num">{formatNumber(p.tagged)}</td>
                {lines.map((l, i) => (
                  <React.Fragment key={series[i].slug}>
                    <td className="trends-table__num">{l[j].rate === null ? "–" : fmtShare(l[j].rate)}</td>
                    <td className="trends-table__num">{formatNumber(l[j].n)}</td>
                  </React.Fragment>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
