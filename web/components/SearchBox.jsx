import React, { useEffect, useId, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { formatNumber } from "../assets/js/format.js";
import Button from "./Button.jsx";
import Popover from "./Popover.jsx";
import "./SearchBox.css";

// Headings and link generators for each kind of suggestion.
const KIND_CONFIG = {
  tag: {
    heading: "Tags",
    // A tag opens the search for its speeches. That page links to the tag page.
    getHref: (item) => `/search?tag=${encodeURIComponent(item.slug)}`,
  },
  place: {
    heading: "Places",
    getHref: (item) => `/place/${item.slug}`,
  },
  subject: {
    heading: "Subjects",
    getHref: (item) => `/search?q=${encodeURIComponent(item.name || item.label || "")}`,
  },
  member: {
    heading: "Members",
    getHref: (item) => `/member/${item.id}`,
  },
};

const KIND_ORDER = ["tag", "place", "subject", "member"];

// Group suggestions by kind, keeping up to 5 items in each group.
function groupSuggestions(results) {
  if (!Array.isArray(results)) {
    return [];
  }

  const groups = new Map();
  for (const item of results) {
    const rawKind = (item.kind || "").toLowerCase().replace(/s$/, "");
    if (!KIND_CONFIG[rawKind]) {
      continue;
    }
    if (!groups.has(rawKind)) {
      groups.set(rawKind, []);
    }
    const list = groups.get(rawKind);
    if (list.length < 5) {
      list.push(item);
    }
  }

  const output = [];
  for (const kind of KIND_ORDER) {
    if (groups.has(kind) && groups.get(kind).length > 0) {
      output.push({
        kind,
        heading: KIND_CONFIG[kind].heading,
        items: groups.get(kind),
      });
    }
  }
  return output;
}

// The SearchBox component renders the main search input with autocomplete suggestions.
export default function SearchBox({ initial = "" }) {
  const [query, setQuery] = useState(initial || "");
  const [results, setResults] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);

  const inputRef = useRef(null);
  // Suggestions open only after the reader types. A page that opens with words in the box shows no list.
  const typedRef = useRef(false);
  const navigate = useNavigate();
  const listboxId = useId();

  // Keep state in sync if initial prop changes.
  useEffect(() => {
    if (initial !== undefined && initial !== null) {
      setQuery(initial);
    }
  }, [initial]);

  // Debounced search call with AbortController cancellation.
  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2 || !typedRef.current) {
      setResults([]);
      setIsOpen(false);
      setSelectedIndex(-1);
      return;
    }

    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const data = await getJSON("/api/search", { q: trimmed }, { signal: controller.signal });
        const rawResults = Array.isArray(data) ? data : data?.results || [];
        setResults(rawResults);
        setIsOpen(rawResults.length > 0);
        setSelectedIndex(-1);
      } catch (err) {
        if (!controller.signal.aborted) {
          setResults([]);
          setIsOpen(false);
        }
      }
    }, 250);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  const grouped = groupSuggestions(results);

  // Flatten suggestions to simplify keyboard navigation and ARIA attributes.
  const flatSuggestions = [];
  let flatIndex = 0;
  for (const group of grouped) {
    const config = KIND_CONFIG[group.kind];
    for (const item of group.items) {
      flatSuggestions.push({
        ...item,
        flatIndex,
        optionId: `${listboxId}-option-${flatIndex}`,
        href: config.getHref(item),
        displayLabel: item.label || item.name || "",
      });
      flatIndex += 1;
    }
  }

  const handleInputChange = (event) => {
    typedRef.current = true;
    setQuery(event.target.value);
  };

  const handleSearchSubmit = (event) => {
    if (event) {
      event.preventDefault();
    }
    setIsOpen(false);
    navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  const handleKeyDown = (event) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      if (!isOpen && flatSuggestions.length > 0) {
        setIsOpen(true);
        setSelectedIndex(0);
        return;
      }
      if (flatSuggestions.length > 0) {
        setSelectedIndex((prev) => (prev + 1) % flatSuggestions.length);
      }
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      if (flatSuggestions.length > 0) {
        setSelectedIndex((prev) => (prev <= 0 ? flatSuggestions.length - 1 : prev - 1));
      }
    } else if (event.key === "Enter") {
      event.preventDefault();
      if (isOpen && selectedIndex >= 0 && flatSuggestions[selectedIndex]) {
        const chosen = flatSuggestions[selectedIndex];
        setIsOpen(false);
        navigate(chosen.href);
      } else {
        handleSearchSubmit();
      }
    } else if (event.key === "Escape") {
      setIsOpen(false);
      setSelectedIndex(-1);
    }
  };

  const activeOptionId =
    selectedIndex >= 0 && flatSuggestions[selectedIndex]
      ? flatSuggestions[selectedIndex].optionId
      : undefined;

  return (
    <form
      role="search"
      className="search-box"
      onSubmit={handleSearchSubmit}
      noValidate
    >
      <div className="search-box__bar">
        <input
          ref={inputRef}
          type="search"
          className="search-box__input"
          placeholder="Search speeches or members"
          value={query}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          role="combobox"
          aria-expanded={isOpen && flatSuggestions.length > 0}
          aria-autocomplete="list"
          aria-controls={listboxId}
          aria-activedescendant={activeOptionId}
        />
        <div className="search-box__button-wrap">
          <Button variant="primary" onClick={handleSearchSubmit}>
            Search
          </Button>
        </div>
      </div>

      <Popover
        open={isOpen && flatSuggestions.length > 0}
        onClose={() => setIsOpen(false)}
        triggerRef={inputRef}
        className="search-box__popover"
      >
        <div role="listbox" id={listboxId} className="search-box__listbox">
          {grouped.map((group) => {
            const config = KIND_CONFIG[group.kind];
            return (
              <div key={group.kind} className="search-box__group">
                <div className="search-box__group-heading" role="presentation">
                  {group.heading}
                </div>
                {group.items.map((item) => {
                  const href = config.getHref(item);
                  const flatItem = flatSuggestions.find((f) => f.href === href && f.name === item.name);
                  const isSelected = flatItem && flatItem.flatIndex === selectedIndex;
                  const optionId = flatItem ? flatItem.optionId : undefined;
                  const countText = formatNumber(item.n_speeches);

                  return (
                    <Link
                      key={`${group.kind}-${item.slug || item.id || item.name}`}
                      to={href}
                      id={optionId}
                      role="option"
                      aria-selected={isSelected}
                      className={`search-box__suggestion ${
                        isSelected ? "search-box__suggestion--selected" : ""
                      }`}
                      onClick={() => setIsOpen(false)}
                    >
                      <span className="search-box__suggestion-name">
                        {item.label || item.name}
                      </span>
                      <span className="search-box__suggestion-count">
                        {countText}
                      </span>
                    </Link>
                  );
                })}
              </div>
            );
          })}
        </div>
      </Popover>
    </form>
  );
}

export { SearchBox };
