import React, { useEffect, useRef, useState } from "react";
import { getJSON } from "../../assets/js/api.js";
import { formatNumber, termShort } from "../../assets/js/format.js";
import Button from "../../components/Button.jsx";
import Popover from "../../components/Popover.jsx";
import { FIELDS, LIST_OPS, addFilterChanges } from "./filterRules.js";

// The value rows of a field whose values the API can list: value, label and count.
function rowsOf(key, facets, named) {
  if (key === "term") return (facets.term || []).slice().sort((a, b) => b.term - a.term).map((r) => ({ value: String(r.term), label: termShort(r.term), n: r.n }));
  if (key === "party") return (facets.party || []).map((r) => ({ value: r.party, label: r.party, n: r.n }));
  if (key === "kind") return (facets.kind || []).map((r) => ({ value: r.kind, label: r.label, n: r.n }));
  if (key === "session") return (facets.session || []).map((r) => ({ value: `${r.term}-${r.session}`, label: `${termShort(r.term)} ${r.label || `session ${r.session}`}`, n: r.n }));
  if (key === "member") return (named || []).map((r) => ({ value: String(r.id), label: r.name, n: r.n }));
  if (key === "subject") return (named || []).map((r) => ({ value: String(r.id), label: r.label, n: r.n }));
  if (key === "tag" || key === "place") return (named || []).map((r) => ({ value: r.slug, label: r.tag, n: r.n }));
  if (key === "state") return (named || []).map((r) => ({ value: r.state, label: r.state, n: r.n }));
  return [];
}

// The editor of a list field: the operator, a box to find a value, and the values.
function ListEditor({ field, params, facets, op, chosen, setChosen }) {
  const [text, setText] = useState("");
  const [named, setNamed] = useState(null);
  const single = LIST_OPS.find((o) => o.value === op).single;

  useEffect(() => {
    if (!field.facet) return undefined;
    const controller = new AbortController();
    getJSON("/api/speeches", { ...params, facets: field.facet, per_page: 1 }, { signal: controller.signal })
      .then((d) => setNamed(d.facets[field.facet]))
      .catch(() => setNamed([]));
    return () => controller.abort();
  }, [field.key]);

  const needle = text.trim().toLowerCase();
  const loading = field.facet && named === null;
  const listed = rowsOf(field.key, facets, named).filter((r) => r.label.toLowerCase().includes(needle));
  const kept = Object.values(chosen).filter((c) => !listed.some((r) => r.value === c.value));
  const rows = [...kept, ...listed];
  const toggle = (row) =>
    setChosen((c) => {
      if (single) return { [row.value]: row };
      const next = { ...c };
      if (next[row.value]) delete next[row.value];
      else next[row.value] = row;
      return next;
    });
  return (
    <>
      <input
        className="search-add__find"
        aria-label={`Find a ${field.label.toLowerCase()}`}
        placeholder={`Find a ${field.label.toLowerCase()}`}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="search-add__values">
        {rows.map((r) => (
          <label key={r.value} className="search-ticks__row search-add__value">
            <input type={single ? "radio" : "checkbox"} name={`add-${field.key}`} checked={!!chosen[r.value]} onChange={() => toggle(r)} />
            <span className="search-ticks__name">{r.label}</span>
            {r.n !== null && r.n !== undefined && <span className="search-ticks__n">{formatNumber(r.n)}</span>}
          </label>
        ))}
        {rows.length === 0 && (
          <p className="search-ticks__note">{loading ? "The list is loading." : "No value matches."}</p>
        )}
      </div>
    </>
  );
}

// The Add filter button and its pop-up. Add runs the search at once, with any waiting ticks.
export default function AddFilter({ params, facets, onAdd }) {
  const [open, setOpen] = useState(false);
  const [fieldKey, setFieldKey] = useState(FIELDS[0].key);
  const [op, setOp] = useState("one_of");
  const [chosen, setChosen] = useState({});
  const trigger = useRef(null);
  const field = FIELDS.find((f) => f.key === fieldKey);

  const close = () => {
    setOpen(false);
    setFieldKey(FIELDS[0].key);
    setOp("one_of");
    setChosen({});
  };
  // A value of one field means nothing in another field, so a new field starts with no ticks.
  const changeField = (key) => {
    setFieldKey(key);
    setChosen({});
  };
  const changeOp = (value) => {
    setOp(value);
    // "is" and "is not" hold one value, so only the first tick stays.
    if (LIST_OPS.find((o) => o.value === value).single) {
      const first = Object.values(chosen)[0];
      setChosen(first ? { [first.value]: first } : {});
    }
  };
  const ready = Object.keys(chosen).length > 0;
  const add = () => {
    onAdd(addFilterChanges(params, fieldKey, op, { values: Object.keys(chosen) }));
    close();
  };

  return (
    <div className="search-add">
      <button ref={trigger} type="button" className="search-add__button" aria-expanded={open} onClick={() => (open ? close() : setOpen(true))}>
        <span>Add filter</span><span aria-hidden="true">+</span>
      </button>
      <Popover open={open} onClose={close} triggerRef={trigger} className="search-add__pop" role="dialog" aria-label="Add a filter">
        <div className="search-add__row">
          <label className="search-add__label">
            Field
            <select className="search-sort__select" value={fieldKey} onChange={(e) => changeField(e.target.value)}>
              {FIELDS.map((f) => <option key={f.key} value={f.key}>{f.label}</option>)}
            </select>
          </label>
          <label className="search-add__label">
            Operator
            <select className="search-sort__select" value={op} onChange={(e) => changeOp(e.target.value)}>
              {LIST_OPS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </label>
        </div>
        <ListEditor key={fieldKey} field={field} params={params} facets={facets} op={op} chosen={chosen} setChosen={setChosen} />
        <div className="search-add__actions">
          <Button variant="secondary" onClick={close}>Cancel</Button>
          <Button variant="primary" disabled={!ready} onClick={add}>Add</Button>
        </div>
      </Popover>
    </div>
  );
}
