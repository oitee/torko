import React, { useEffect, useId, useState } from "react";
import { getJSON } from "../../assets/js/api.js";
import { formatNumber } from "../../assets/js/format.js";

// The kinds that the picker offers, the word that names each kind, and the address key that it sets.
const KINDS = {
  tag: { word: "Tag", key: "tag", value: (r) => r.slug },
  place: { word: "Place", key: "place", value: (r) => r.slug },
  member: { word: "Member", key: "member", value: (r) => String(r.id) },
};
const MAX = 8;

// SearchScopePicker narrows the speeches to one tag, one place or one member.
// The reader types a name and picks one match. The page then sets tag, place or member in the address.
export default function SearchScopePicker({ onPick }) {
  const [text, setText] = useState("");
  const [options, setOptions] = useState([]);
  const [active, setActive] = useState(-1);
  const [open, setOpen] = useState(false);
  const listId = useId();

  useEffect(() => {
    const q = text.trim();
    if (q.length < 2) {
      setOptions([]);
      setOpen(false);
      return undefined;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      getJSON("/api/search", { q }, { signal: controller.signal })
        .then((data) => {
          const rows = (data?.results || []).filter((r) => KINDS[r.kind]).slice(0, MAX);
          setOptions(rows);
          setActive(rows.length ? 0 : -1);
          setOpen(true);
        })
        .catch(() => {
          if (!controller.signal.aborted) setOptions([]);
        });
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [text]);

  const pick = (row) => {
    const kind = KINDS[row.kind];
    onPick({ [kind.key]: kind.value(row) });
    setText("");
    setOpen(false);
  };

  const onKeyDown = (e) => {
    if (e.key === "ArrowDown" && options.length) {
      e.preventDefault();
      setOpen(true);
      setActive((i) => (i + 1) % options.length);
    } else if (e.key === "ArrowUp" && options.length) {
      e.preventDefault();
      setActive((i) => (i <= 0 ? options.length - 1 : i - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (open && options[active]) pick(options[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const showList = open && text.trim().length >= 2;
  const optionId = (i) => `${listId}-o${i}`;

  return (
    <div className="search-pick">
      <label className="search-pick__label" htmlFor={`${listId}-input`}>
        Tag, place or member
      </label>
      <div className="search-pick__field">
        <input
          id={`${listId}-input`}
          className="search-pick__input"
          type="text"
          autoComplete="off"
          placeholder="For example Farmers or Latur"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          onBlur={() => setTimeout(() => setOpen(false), 150)}
          onFocus={() => options.length && setOpen(true)}
          role="combobox"
          aria-expanded={showList}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={showList && active >= 0 ? optionId(active) : undefined}
        />
        {showList && (
          <ul id={listId} role="listbox" className="search-pick__list">
            {options.length === 0 ? (
              <li className="search-pick__none">No tag, place or member has this name.</li>
            ) : (
              options.map((row, i) => (
                <li
                  key={`${row.kind}-${row.slug || row.id}`}
                  id={optionId(i)}
                  role="option"
                  aria-selected={i === active}
                  className={`search-pick__option ${i === active ? "search-pick__option--active" : ""}`}
                  onMouseDown={(e) => {
                    e.preventDefault();
                    pick(row);
                  }}
                  onMouseEnter={() => setActive(i)}
                >
                  <span className="search-pick__kind">{KINDS[row.kind].word}</span>
                  <span className="search-pick__name">{row.name}</span>
                  <span className="search-pick__n">{formatNumber(row.n_speeches)}</span>
                </li>
              ))
            )}
          </ul>
        )}
      </div>
    </div>
  );
}
