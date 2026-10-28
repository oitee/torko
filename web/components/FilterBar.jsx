import React, { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { termShort } from "../assets/js/format.js";
import Button from "./Button.jsx";
import Chip from "./Chip.jsx";
import Count from "./Count.jsx";
import Popover from "./Popover.jsx";
import "./FilterBar.css";

const DEFAULT_GROUPS = ["term", "party", "kind", "subject"];

const GROUP_TITLES = {
  term: "Term",
  party: "Party",
  kind: "Type",
  subject: "Subject",
  session: "Session",
};

// Extract label, value, and count for an item in a facet group.
function getItemInfo(groupKey, item) {
  if (!item) {
    return { label: "", value: "", count: null };
  }
  const count = item.n !== undefined ? item.n : item.count;
  switch (groupKey) {
    case "term":
      return {
        label: termShort(item.term),
        value: String(item.term),
        count,
      };
    case "party":
      return {
        label: String(item.party),
        value: String(item.party),
        count,
      };
    case "kind":
      return {
        label: String(item.label || item.kind),
        value: String(item.kind),
        count,
      };
    case "subject":
      return {
        label: String(item.label || item.name || item.id),
        value: String(item.id !== undefined ? item.id : item.subject || item.label),
        count,
      };
    case "session": {
      const fallback = item.term && item.session ? `${item.term}-${item.session}` : "";
      return {
        label: String(item.label || fallback),
        value: item.term && item.session ? `${item.term}-${item.session}` : String(item.session || item.term),
        count,
      };
    }
    default:
      return {
        label: String(item.label || item.name || item[groupKey] || ""),
        value: String(item.id !== undefined ? item.id : item[groupKey] || item.label || ""),
        count,
      };
  }
}

// The FilterBar component displays facets as interactive chips.
// It manages filters in the URL address with comma-separated values.
export default function FilterBar({
  facets = {},
  total,
  unfilteredTotal,
  noun = "speeches",
  groups = DEFAULT_GROUPS,
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const [expandedGroups, setExpandedGroups] = useState({});
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const mobileTriggerRef = useRef(null);
  const copyTimerRef = useRef(null);

  // Filter out any group with no rows in facets.
  const visibleGroups = (groups || DEFAULT_GROUPS).filter(
    (g) => Array.isArray(facets?.[g]) && facets[g].length > 0
  );

  // Compute active filters and total count of selected filter choices.
  const activeFilters = {};
  let activeFilterCount = 0;

  const allPossibleKeys = new Set([
    ...DEFAULT_GROUPS,
    ...(groups || []),
    ...Object.keys(facets || {}),
  ]);

  for (const key of allPossibleKeys) {
    const raw = searchParams.get(key);
    if (raw) {
      const values = raw
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean);
      if (values.length > 0) {
        activeFilters[key] = values;
        activeFilterCount += values.length;
      }
    }
  }

  useEffect(() => {
    return () => {
      clearTimeout(copyTimerRef.current);
    };
  }, []);

  const toggleFilter = (groupKey, itemValue) => {
    const strVal = String(itemValue);
    const current = (searchParams.get(groupKey) || "")
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);

    let next;
    if (current.includes(strVal)) {
      next = current.filter((v) => v !== strVal);
    } else {
      next = [...current, strVal];
    }

    const newParams = new URLSearchParams(searchParams);
    if (next.length > 0) {
      newParams.set(groupKey, next.join(","));
    } else {
      newParams.delete(groupKey);
    }
    // Changing any filter resets pagination back to page 1.
    newParams.delete("page");
    setSearchParams(newParams);
  };

  const handleResetFilters = () => {
    const newParams = new URLSearchParams(searchParams);
    for (const key of allPossibleKeys) {
      newParams.delete(key);
    }
    newParams.delete("page");
    setSearchParams(newParams);
  };

  const handleCopyLink = () => {
    try {
      if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
        navigator.clipboard.writeText(window.location.href).catch(() => {});
      }
    } catch {
      // Ignore clipboard write failures.
    }
    setCopied(true);
    clearTimeout(copyTimerRef.current);
    copyTimerRef.current = setTimeout(() => {
      setCopied(false);
    }, 2000);
  };

  const toggleGroupExpand = (groupKey) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [groupKey]: !prev[groupKey],
    }));
  };

  // Render the choice chips for all visible groups.
  const renderFilterGroups = () => {
    return (
      <div className="filter-bar__groups">
        {visibleGroups.map((groupKey) => {
          const rows = facets[groupKey] || [];
          const isExpanded = !!expandedGroups[groupKey];
          const displayedRows = isExpanded ? rows : rows.slice(0, 8);
          const hasMore = rows.length > 8;
          const title =
            GROUP_TITLES[groupKey] ||
            groupKey.charAt(0).toUpperCase() + groupKey.slice(1);
          const currentActive = activeFilters[groupKey] || [];

          return (
            <div key={groupKey} className="filter-bar__group">
              <span className="filter-bar__group-title">{title}</span>
              <div className="filter-bar__choices">
                {displayedRows.map((item, index) => {
                  const { label, value, count } = getItemInfo(groupKey, item);
                  const isSelected = currentActive.includes(value);

                  return (
                    <button
                      key={`${groupKey}-${value}-${index}`}
                      type="button"
                      className="filter-bar__chip-btn"
                      onClick={() => toggleFilter(groupKey, value)}
                      aria-pressed={isSelected}
                    >
                      <Chip
                        label={label}
                        count={count}
                        selected={isSelected}
                      />
                    </button>
                  );
                })}
                {hasMore && (
                  <Button
                    variant="text"
                    onClick={() => toggleGroupExpand(groupKey)}
                  >
                    {isExpanded ? "Show fewer" : `Show all ${rows.length}`}
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // The total with no filter comes from the page. The bar does not guess it, because a page can open with filters on.
  const effectiveUnfilteredTotal = unfilteredTotal ?? null;

  return (
    <nav className="filter-bar" aria-label="Filters">
      {/* Desktop view: filter groups displayed in flow */}
      <div className="filter-bar__desktop-groups">
        {renderFilterGroups()}
      </div>

      {/* Mobile view trigger: collapses into Filters · N button below 768px */}
      <div className="filter-bar__mobile-trigger-wrap">
        <div ref={mobileTriggerRef} className="filter-bar__mobile-trigger-inner">
          <Button
            variant="secondary"
            onClick={() => setIsMobileOpen((prev) => !prev)}
          >
            {`Filters · ${activeFilterCount}`}
          </Button>
        </div>
      </div>

      {/* Mobile filter sheet popover */}
      <Popover
        open={isMobileOpen}
        onClose={() => setIsMobileOpen(false)}
        triggerRef={mobileTriggerRef}
        className="filter-bar__sheet"
        role="dialog"
        aria-label="Filter choices"
      >
        <div className="filter-bar__sheet-header">
          <span className="filter-bar__sheet-title">
            {`Filters · ${activeFilterCount}`}
          </span>
          <Button variant="text" onClick={() => setIsMobileOpen(false)}>
            Close
          </Button>
        </div>
        <div className="filter-bar__sheet-content">
          {renderFilterGroups()}
        </div>
        {activeFilterCount > 0 && (
          <div className="filter-bar__sheet-footer">
            <Button variant="secondary" onClick={handleResetFilters}>
              Reset filters
            </Button>
          </div>
        )}
      </Popover>

      {/* Summary row: stays visible outside the mobile sheet */}
      <div className="filter-bar__summary">
        <div className="filter-bar__count">
          {activeFilterCount > 0 && effectiveUnfilteredTotal !== null && effectiveUnfilteredTotal !== undefined ? (
            <Count n={total} total={effectiveUnfilteredTotal} noun={noun} />
          ) : (
            <Count n={total} noun={noun} />
          )}
        </div>

        <Button variant="text" onClick={handleCopyLink}>
          {copied ? "Link copied" : "Copy link"}
        </Button>

        {activeFilterCount > 0 && (
          <Button variant="secondary" onClick={handleResetFilters}>
            Reset filters
          </Button>
        )}
      </div>
    </nav>
  );
}

export { FilterBar };
