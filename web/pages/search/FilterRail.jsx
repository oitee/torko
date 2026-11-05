import React, { useState } from "react";
import { formatNumber, termShort } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";
import AddFilter from "./AddFilter.jsx";
import { MAX_YEAR, MIN_YEAR, TERMS, listOf, pendingCount, yearsFrom } from "./filterRules.js";

const SHORT_LIST = 6;

// One group of tick boxes. A box whose value is in an "is none of" chip stays empty and locked.
function TickGroup({ title, rows, field, draft, setDraft, locked }) {
  const [more, setMore] = useState(false);
  const shown = more ? rows : rows.filter((r, i) => i < SHORT_LIST || draft[field].includes(r.value));
  const toggle = (value) =>
    setDraft((d) => ({
      ...d,
      [field]: d[field].includes(value) ? d[field].filter((v) => v !== value) : [...d[field], value],
    }));
  return (
    <fieldset className="search-ticks">
      <legend className="search-ticks__title">{title}</legend>
      {shown.map((r) => {
        // A value with no speeches cannot be ticked. A ticked one stays open, so that the reader can untick it.
        const isLocked = locked.includes(r.value) || (r.n === 0 && !draft[field].includes(r.value));
        return (
          <label key={r.value} className={`search-ticks__row ${r.n === 0 || isLocked ? "search-ticks__row--off" : ""}`}>
            <input type="checkbox" checked={!isLocked && draft[field].includes(r.value)} disabled={isLocked} onChange={() => toggle(r.value)} />
            <span className="search-ticks__name">{r.label}</span>
            {r.n !== null && r.n !== undefined && <span className="search-ticks__n">{formatNumber(r.n)}</span>}
          </label>
        );
      })}
      {rows.length > SHORT_LIST && (
        <Button variant="text" onClick={() => setMore((m) => !m)}>
          {more ? "Show fewer" : `Show all ${rows.length}`}
        </Button>
      )}
    </fieldset>
  );
}

// Two sliders for the years of the debate date. They wait for Apply, as the boxes do.
function DateYears({ params, draft, setDraft }) {
  const [from, to] = draft.years || yearsFrom(params);
  const set = (a, b) => setDraft((d) => ({ ...d, years: [a, b] }));
  return (
    <fieldset className="search-ticks">
      <legend className="search-ticks__title">Date</legend>
      <p className="search-years__span">{from === to ? from : `${from} to ${to}`}</p>
      <label className="search-years__row">
        <span>From year</span>
        <input type="range" min={MIN_YEAR} max={MAX_YEAR} value={from} onChange={(e) => { const a = Number(e.target.value); set(a, Math.max(a, to)); }} />
      </label>
      <label className="search-years__row">
        <span>To year</span>
        <input type="range" min={MIN_YEAR} max={MAX_YEAR} value={to} onChange={(e) => { const b = Number(e.target.value); set(Math.min(from, b), b); }} />
      </label>
    </fieldset>
  );
}

// Keep every ticked value in the list, also when the counts do not hold it.
function withTicked(rows, ticked, nameOf) {
  const have = new Set(rows.map((r) => r.value));
  return [...rows, ...ticked.filter((v) => !have.has(v)).map((v) => ({ value: v, label: nameOf(v), n: null }))];
}

// The left panel: Add filter first, then the four main fields, then the bar that applies the waiting changes.
export default function FilterRail({ params, facets, tagRows, names, chipCount, draft, setDraft, onApply, onDiscard, onAdd }) {
  const [open, setOpen] = useState(false);
  const pending = pendingCount(draft, params);
  const terms = TERMS.map((t) => ({ value: String(t), label: termShort(t), n: (facets.term || []).find((r) => r.term === t)?.n ?? (facets.term ? 0 : null) }));
  const parties = (facets.party || []).map((p) => ({ value: p.party, label: p.party, n: p.n }));
  const tags = (tagRows || []).map((t) => ({ value: t.slug, label: t.tag, n: t.n }));
  return (
    <div className={`search-filters ${open ? "search-filters--open" : ""}`}>
      <div className="search-filters__phone">
        <Button variant="secondary" aria-expanded={open} onClick={() => setOpen((o) => !o)}>{`Filters · ${chipCount}`}</Button>
      </div>
      <div className="search-filters__body">
        <AddFilter params={params} facets={facets} onAdd={onAdd} />
        <TickGroup title="Tag" field="tag" rows={withTicked(tags, draft.tag, (v) => names.slug?.[v] || v)} draft={draft} setDraft={setDraft} locked={listOf(params.tag_not)} />
        <DateYears params={params} draft={draft} setDraft={setDraft} />
        <TickGroup title="Term" field="term" rows={terms} draft={draft} setDraft={setDraft} locked={listOf(params.term_not)} />
        <TickGroup title="Party" field="party" rows={withTicked(parties, draft.party, (v) => v)} draft={draft} setDraft={setDraft} locked={listOf(params.party_not)} />
        {pending > 0 && (
          <div className="search-apply" role="status">
            <span className="search-apply__text">{pending === 1 ? "1 change not applied yet" : `${pending} changes not applied yet`}</span>
            <div className="search-apply__actions">
              <Button variant="primary" onClick={onApply}>Apply</Button>
              <Button variant="secondary" onClick={onDiscard}>Discard changes</Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
