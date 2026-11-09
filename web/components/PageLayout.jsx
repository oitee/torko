import React from "react";
import Margin from "./Margin.jsx";
import "./PageLayout.css";

// PageLayout provides the shared grid structure for all content pages.
// It lays out the breadcrumb, answer, main column, and margin.
// A text page (a speech, a debate) puts its counts, method and source in the margin, next to the text.
// A data page puts them in notes: one band under the main column, just above the footer.
export default function PageLayout({ breadcrumb, answer, margin, notes, children }) {
  let marginElement = null;
  if (margin) {
    const isMarginElement =
      React.isValidElement(margin) &&
      (margin.type === Margin || margin.type?.name === "Margin");
    marginElement = isMarginElement ? margin : <Margin>{margin}</Margin>;
  }

  return (
    <div className="page-layout">
      {(breadcrumb || answer) && (
        <div className="page-layout__head">
          {breadcrumb && (
            <div className="page-layout__breadcrumb">{breadcrumb}</div>
          )}
          {answer && <div className="page-layout__answer">{answer}</div>}
        </div>
      )}
      <div
        className={`page-layout__grid ${
          margin ? "page-layout__grid--with-margin" : ""
        }`}
      >
        {marginElement && (
          <aside className="page-layout__margin" aria-label="Page margin">
            {marginElement}
          </aside>
        )}
        <div className="page-layout__main">{children}</div>
      </div>
      {notes && (
        <section className="page-layout__notes" aria-label="Counts, method and source">
          {notes}
        </section>
      )}
    </div>
  );
}

export { PageLayout };
