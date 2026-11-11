// The pure rules of the Search filters: the fields, their operators, the chips, and the ticks that wait for Apply.
import { formatDateLong, formatNumber, termShort } from "../../assets/js/format.js";

export const MIN_YEAR = 1999;
export const MAX_YEAR = 2026;
export const TERMS = [18, 17, 16, 15, 14, 13];

// The four operators of a list field. "is" and "is not" take one value, so they use radio buttons.
export const LIST_OPS = [
  { value: "is", label: "is", single: true },
  { value: "not", label: "is not", single: true, exclude: true },
  { value: "one_of", label: "is one of" },
  { value: "none_of", label: "is none of", exclude: true },
];
// Each field of the Add filter pop-up. Every field offers a list of values. A field that cannot show a list is not here.
// facet is the name that the API gives the list. With no facet, the list comes from the counts that the page already has.
export const FIELDS = [
  { key: "member", label: "Member", facet: "member" },
  { key: "party", label: "Party" },
  { key: "state", label: "State", facet: "state" },
  { key: "term", label: "Term" },
  { key: "session", label: "Session" },
  { key: "tag", label: "Tag", facet: "tag_all" },
  { key: "subject", label: "Subject", facet: "subject_all" },
  { key: "place", label: "Place", facet: "place" },
  { key: "kind", label: "Debate type" },
];

// An old link can still hold a seat or a language, so a chip can still name them. The pop-up does not offer them.
const FIELD_LABELS = { ...Object.fromEntries(FIELDS.map((f) => [f.key, f.label])), seat: "Seat", lang: "Spoken in" };

export const listOf = (value) => String(value || "").split(",").map((s) => s.trim()).filter(Boolean);

// The address key that an operator of a list field writes. With tags, tag means all of them and tag_any means one of them.
function listKey(field, op) {
  if (op === "not" || op === "none_of") return `${field}_not`;
  if (field === "tag" && op === "one_of") return "tag_any";
  return field;
}

// The address changes of one filter from the pop-up. A value moves out of the opposite list, so that two chips never disagree.
export function addFilterChanges(params, fieldKey, op, input) {
  const key = listKey(fieldKey, op);
  const keys = fieldKey === "tag" ? ["tag", "tag_any", "tag_not"] : [fieldKey, `${fieldKey}_not`];
  const changes = {};
  for (const other of keys) {
    if (other === key) continue;
    const left = listOf(params[other]).filter((v) => !input.values.includes(v));
    if (left.length !== listOf(params[other]).length) changes[other] = left.join(",") || null;
  }
  changes[key] = [...new Set([...listOf(params[key]), ...input.values])].join(",");
  return changes;
}

function dateChip(from, to) {
  const yearFrom = from && from.endsWith("-01-01") ? from.slice(0, 4) : null;
  const yearTo = to && to.endsWith("-12-31") ? to.slice(0, 4) : null;
  if (from && to && from === to) return `is on ${formatDateLong(from)}`;
  if (from && to) return yearFrom && yearTo ? `is between ${yearFrom} and ${yearTo}` : `is between ${formatDateLong(from)} and ${formatDateLong(to)}`;
  if (from) return yearFrom ? `is in ${yearFrom} or later` : `is on or after ${formatDateLong(from)}`;
  return yearTo ? `is in ${yearTo} or earlier` : `is on or before ${formatDateLong(to)}`;
}

// Past three values, a chip shows two and the number of the others.
function shortList(names) {
  return names.length > 3 ? `${names.slice(0, 2).join(", ")} +${names.length - 2}` : names.join(", ");
}

// One chip for each field and operator. A chip that leaves speeches out has negative set.
// names gives { slug, member, subject, kind, session } maps from a value to its name.
export function chipsFrom(params, names = {}) {
  const show = {
    term: termShort,
    tag: (v) => names.slug?.[v] || v,
    place: (v) => names.slug?.[v] || v,
    member: (v) => names.member?.[v] || `Member ${v}`,
    subject: (v) => names.subject?.[v] || `Subject ${v}`,
    kind: (v) => names.kind?.[v] || v,
    session: (v) => names.session?.[v] || v,
    lang: (v) => ({ en: "English", hi: "Hindi", mixed: "Mixed" }[v] || v),
  };
  const chips = [];
  const push = (key, field, one, many, negative = false) => {
    const values = listOf(params[key]);
    if (!values.length) return;
    const shown = values.map(show[field] || ((v) => v));
    const words = values.length > 1 ? many : one;
    chips.push({ key, label: `${FIELD_LABELS[field]} ${words} ${shortList(shown)}`, negative, remove: { [key]: null } });
  };
  push("tag", "tag", "is", "is");
  push("tag_any", "tag", "is", "is one of");
  push("tag_not", "tag", "is not", "is none of", true);
  for (const f of ["member", "party", "state", "seat", "term", "session", "subject", "place", "kind", "lang"]) {
    push(f, f, "is", "is one of");
    push(`${f}_not`, f, "is not", "is none of", true);
  }
  if (params.date_from || params.date_to) {
    chips.push({ key: "date", label: `Date ${dateChip(params.date_from, params.date_to)}`, remove: { date_from: null, date_to: null } });
  }
  if (params.min_words || params.max_words) {
    const a = params.min_words && formatNumber(Number(params.min_words));
    const b = params.max_words && formatNumber(Number(params.max_words));
    const words = a && b ? `is between ${a} and ${b}` : a ? `is at least ${a}` : `is at most ${b}`;
    chips.push({ key: "words", label: `Words in the speech ${words}`, remove: { min_words: null, max_words: null } });
  }
  if (params.title) chips.push({ key: "title", label: `Debate title contains ${params.title}`, remove: { title: null } });
  if (params.title_not) chips.push({ key: "title_not", label: `Debate title does not contain ${params.title_not}`, negative: true, remove: { title_not: null } });
  return chips;
}

// The ticks of the left panel start from the address. They change the address only on Apply, on Add, or when a chip goes.
export function draftFrom(params) {
  return { tag: listOf(params.tag), party: listOf(params.party), term: listOf(params.term), years: null };
}

export function yearsFrom(params) {
  return [
    params.date_from ? Number(params.date_from.slice(0, 4)) : MIN_YEAR,
    params.date_to ? Number(params.date_to.slice(0, 4)) : MAX_YEAR,
  ];
}

// The number of ticks and sliders that differ from the address.
export function pendingCount(draft, params) {
  let n = 0;
  for (const k of ["tag", "party", "term"]) {
    const now = listOf(params[k]);
    n += draft[k].filter((v) => !now.includes(v)).length + now.filter((v) => !draft[k].includes(v)).length;
  }
  return n + (draft.years ? 1 : 0);
}

// The address changes that the waiting ticks make.
export function draftChanges(draft) {
  const changes = {
    tag: draft.tag.join(",") || null,
    party: draft.party.join(",") || null,
    term: draft.term.join(",") || null,
  };
  if (draft.years) {
    changes.date_from = draft.years[0] > MIN_YEAR ? `${draft.years[0]}-01-01` : null;
    changes.date_to = draft.years[1] < MAX_YEAR ? `${draft.years[1]}-12-31` : null;
  }
  return changes;
}
