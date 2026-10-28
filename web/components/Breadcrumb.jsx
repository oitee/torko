import React from "react";
import { Link } from "react-router-dom";
import "./Breadcrumb.css";

// The Breadcrumb component shows the path to the current page.
// The current item has no link and carries aria-current="page".
// On phones it collapses middle items when there are more than 3 items.
export default function Breadcrumb({ items }) {
  if (!items || items.length === 0) {
    return null;
  }

  const hasCollapse = items.length > 3;
  const lastIndex = items.length - 1;

  return (
    <nav aria-label="Breadcrumb" className="breadcrumb">
      <ol className="breadcrumb__list">
        {items.map((item, index) => {
          const isFirst = index === 0;
          const isLast = index === lastIndex;
          // Only a breadcrumb that collapses on phones hides its middle items.
          const isMiddle = hasCollapse && !isFirst && !isLast;

          if (isLast) {
            return (
              <React.Fragment key={index}>
                {hasCollapse && (
                  <li
                    className="breadcrumb__item breadcrumb__item--collapsed"
                    aria-hidden="true"
                  >
                    <span className="breadcrumb__ellipsis">…</span>
                    <span className="breadcrumb__separator">/</span>
                  </li>
                )}
                <li className="breadcrumb__item breadcrumb__item--current">
                  <span aria-current="page" className="breadcrumb__current">
                    {item.label}
                  </span>
                </li>
              </React.Fragment>
            );
          }

          const itemClass = isMiddle
            ? "breadcrumb__item breadcrumb__item--middle"
            : "breadcrumb__item";

          return (
            <li key={index} className={itemClass}>
              {item.href ? (
                <Link to={item.href} className="breadcrumb__link">
                  {item.label}
                </Link>
              ) : (
                <span className="breadcrumb__text">{item.label}</span>
              )}
              <span aria-hidden="true" className="breadcrumb__separator">
                /
              </span>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export { Breadcrumb };
