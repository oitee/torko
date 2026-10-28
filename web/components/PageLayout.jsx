import React from "react";
import Margin from "./Margin.jsx";
import "./PageLayout.css";

// PageLayout provides the shared grid structure for all content pages.
// It lays out the breadcrumb, answer, main column, and margin.
export default function PageLayout({ breadcrumb, answer, margin, children }) {
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
    </div>
  );
}

export { PageLayout };
