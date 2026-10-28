import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { formatNumber, termShort } from "../assets/js/format.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import Chip from "../components/Chip.jsx";
import FilterBar from "../components/FilterBar.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageLayout from "../components/PageLayout.jsx";
import SearchBox from "../components/SearchBox.jsx";
import SearchMatches from "./search/SearchMatches.jsx";
import SearchResults from "./search/SearchResults.jsx";
import SearchScopeCard from "./search/SearchScopeCard.jsx";
import SearchScopePicker from "./search/SearchScopePicker.jsx";
import { FILTER_KEYS, headingParts, readSearch, selectedTerms } from "./search/searchParams.js";
import "./search.css";

const PER_PAGE = 20;

// Where the name of a scope comes from, for the heading and the scope chip.
const SCOPE_NAME_URL = {
  tag: (v) => `/api/tag/${encodeURIComponent(v)}`,
  place: (v) => `/api/place/${encodeURIComponent(v)}`,
  member: (v) => `/api/member/${encodeURIComponent(v)}`,
};

// Run one API call when its key changes. Keep the last answer while the next one loads.
function useApi(key, load) {
  const [state, setState] = useState({ data: null, loading: Boolean(key), error: null });
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    if (!key) {
      setState({ data: null, loading: false, error: null });
      return undefined;
    }
    const controller = new AbortController();
    setState((s) => ({ ...s, loading: true, error: null }));
    load(controller.signal)
      .then((data) => setState({ data, loading: false, error: null }))
      .catch((error) => {
        if (!controller.signal.aborted) setState((s) => ({ ...s, loading: false, error }));
      });
    return () => controller.abort();
  }, [key, retry]);
  return { ...state, retry: () => setRetry((n) => n + 1) };
}

// The Search page: the speeches that contain the words, the pages whose names match, and filters.
export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { scope, filters, view, sort, page } = readSearch(searchParams);
  const q = scope.q || "";
  const hasFilters = Object.keys(filters).length > 0;

  const listParams = { ...scope, ...filters, sort, page, per_page: PER_PAGE };
  const listKey = JSON.stringify({ listParams, view });
  const list = useApi(listKey, (signal) =>
    getJSON("/api/speeches", { ...listParams, ...(view === "members" ? { group: "member" } : { facets: 1 }) }, { signal })
  );

  // The facets come with the speech list. The members view asks for them in a small call of its own.
  const facetParams = { ...scope, ...filters, facets: 1, per_page: 1 };
  const facetCall = useApi(view === "members" ? JSON.stringify(facetParams) : null, (signal) =>
    getJSON("/api/speeches", facetParams, { signal })
  );
  const speechData = view === "members" ? facetCall.data : list.data;

  // The total with no filter, for "N of total".
  const baseKey = hasFilters ? JSON.stringify(scope) : null;
  const base = useApi(baseKey, (signal) => getJSON("/api/speeches", { ...scope, per_page: 1 }, { signal }));

  // The number of members, for the toggle. It is a separate call, so the speeches do not wait for it.
  const membersParams = { ...scope, ...filters, group: "member", per_page: 1 };
  const membersCall = useApi(view === "speeches" ? JSON.stringify(membersParams) : null, (signal) =>
    getJSON("/api/speeches", membersParams, { signal })
  );

  const matches = useApi(q || null, (signal) => getJSON("/api/search", { q }, { signal }));
  // The tag, place and member each load their own name, so that they can be on at the same time.
  const useScope = (k) =>
    useApi(scope[k] ? `${k}:${scope[k]}` : null, (signal) => getJSON(SCOPE_NAME_URL[k](scope[k]), undefined, { signal }));
  const scopeInfo = { tag: useScope("tag"), place: useScope("place"), member: useScope("member") };
  const scopeNames = Object.fromEntries(Object.entries(scopeInfo).map(([k, v]) => [k, v.data?.name || null]));

  const speechTotal = speechData && !(view === "speeches" && list.loading) ? speechData.total : null;
  const membersTotal =
    view === "members" ? (list.loading ? null : list.data?.members_total ?? null) : membersCall.loading ? null : membersCall.data?.members_total ?? null;
  const unfilteredTotal = hasFilters ? base.data?.total ?? null : speechTotal;

  useEffect(() => {
    document.title = q ? `${q} · Search · Torko` : "Search · Torko";
  }, [q]);

  // Change some keys of the address. Any change other than the page goes back to page 1.
  const hrefWith = (changes) => {
    const next = new URLSearchParams(searchParams);
    for (const [k, v] of Object.entries(changes)) {
      if (v === null || v === undefined || v === "") next.delete(k);
      else next.set(k, String(v));
    }
    if (!("page" in changes)) next.delete("page");
    const qs = next.toString();
    return qs ? `/search?${qs}` : "/search";
  };
  const setWith = (changes) => {
    const next = new URLSearchParams(hrefWith(changes).split("?")[1] || "");
    setSearchParams(next);
  };
  const resetFilters = () => setWith(Object.fromEntries(FILTER_KEYS.map((k) => [k, null])));

  // Session choices only help when one or two terms are chosen.
  const terms = selectedTerms(filters);
  const facets = speechData?.facets || {};
  const groups = ["term", ...(terms.length > 0 && terms.length <= 2 ? ["session"] : []), "party", "kind", "subject"];
  const barFacets = {
    ...facets,
    session: (facets.session || []).filter((s) => terms.includes(s.term)),
    // An empty group shows nothing, but it lets "Reset filters" clear party_not too.
    party_not: [],
  };

  const heading = headingParts({ scope, count: speechTotal, names: scopeNames });
  const csvHref = `/api/speeches?${new URLSearchParams(
    Object.entries({ ...scope, ...filters, sort, format: "csv" })
  ).toString()}`;

  const answer = (
    <div className="search-head">
      <h1 className="search-head__title">
        {heading.lead !== null && <span className="search-head__count">{formatNumber(heading.lead)}</span>}
        {heading.rest}
      </h1>
      <div className="search-head__box">
        <SearchBox key={q} initial={q} />
      </div>
      <ActiveChips scope={scope} scopeNames={scopeNames} filters={filters} facets={facets} setWith={setWith} />
    </div>
  );

  return (
    <PageLayout breadcrumb={<Breadcrumb items={[{ label: "Search" }]} />} answer={answer}>
      <div className="search-body">
        <aside className="search-rail" aria-label="Filters and method">
          <div className="search-rail__section">
            <h2 className="search-rail__title">Narrow the speeches</h2>
            <SearchScopePicker onPick={setWith} />
            {speechData ? (
              <FilterBar
                facets={barFacets}
                groups={groups}
                total={speechTotal ?? speechData.total}
                unfilteredTotal={unfilteredTotal}
                noun="speeches"
              />
            ) : (
              <p className="search-rail__wait">The filters show when the speeches load.</p>
            )}
            {speechData && (
              <LeaveOutParty parties={facets.party || []} filters={filters} setWith={setWith} />
            )}
            <a className="search-rail__csv" href={csvHref} download>
              Download these speeches as CSV
            </a>
          </div>
          <div className="search-rail__section">
            <HowTorkoCounts>
              {q
                ? "A speech matches when one of its own turns has every word of the search. Words that another member says in an interruption do not count. "
                : ""}
              Each speech counts once. The counts by party leave out the speeches with no identified member.
            </HowTorkoCounts>
          </div>
        </aside>

        <div className="search-main">
          {(scope.tag || scope.place) && (
            <div className="search-scopes">
              {["tag", "place"].map((k) =>
                scope[k] ? <SearchScopeCard key={k} kind={k} value={scope[k]} info={scopeInfo[k].data} /> : null
              )}
            </div>
          )}
          {q && matches.data && <SearchMatches results={matches.data.results} query={q} />}
          <SearchResults
            view={view}
            sort={sort}
            page={page}
            data={list.data}
            loading={list.loading}
            error={list.error}
            onRetry={list.retry}
            speechTotal={speechTotal}
            membersTotal={membersTotal}
            viewHref={(v) => hrefWith({ view: v === "speeches" ? null : v })}
            pageHref={(p) => hrefWith({ page: p > 1 ? p : null })}
            memberHref={(id) => hrefWith({ member: id, view: null, tag: scope.tag, place: scope.place })}
            onSort={(s) => setWith({ sort: s === "latest" ? null : s })}
            hasFilters={hasFilters}
            onReset={resetFilters}
          />
        </div>
      </div>
    </PageLayout>
  );
}

// The scope and the filters that are on, as chips that remove themselves.
function ActiveChips({ scope, scopeNames, filters, facets, setWith }) {
  const chips = [];
  for (const k of ["tag", "place", "member"]) {
    if (scope[k]) {
      const what = { tag: "Tag", place: "Place", member: "Member" }[k];
      chips.push({ key: k, label: `${what}: ${scopeNames[k] || scope[k]}`, remove: { [k]: null } });
    }
  }
  const list = (k) => (filters[k] || "").split(",").filter(Boolean);
  const removeOne = (k, v) => ({ [k]: list(k).filter((x) => x !== v).join(",") || null });
  for (const v of list("term")) chips.push({ key: `term-${v}`, label: termShort(v), remove: removeOne("term", v) });
  for (const v of list("session")) {
    const [t, n] = v.split("-");
    const row = (facets.session || []).find((r) => String(r.term) === t && String(r.session) === n);
    chips.push({ key: `session-${v}`, label: row?.label || `${termShort(t)} session ${n}`, remove: removeOne("session", v) });
  }
  for (const v of list("party")) chips.push({ key: `party-${v}`, label: v, remove: removeOne("party", v) });
  for (const v of list("party_not")) chips.push({ key: `not-${v}`, label: `Not ${v}`, remove: removeOne("party_not", v) });
  // A kind or a subject shows its name from the facets. Before they load, it shows the value of the address.
  const nameOf = (rows, key, v) => (rows || []).find((r) => String(r[key]) === v)?.label || v;
  for (const v of list("kind")) chips.push({ key: `kind-${v}`, label: nameOf(facets.kind, "kind", v), remove: removeOne("kind", v) });
  for (const v of list("subject")) chips.push({ key: `subject-${v}`, label: nameOf(facets.subject, "id", v), remove: removeOne("subject", v) });

  if (chips.length === 0) return null;
  return (
    <div className="search-head__active" aria-label="Filters that are on">
      <span className="search-head__active-label">Only</span>
      {chips.map((c) => (
        <Chip key={c.key} label={c.label} selected onRemove={() => setWith(c.remove)} />
      ))}
    </div>
  );
}

// "Leave out a party": one select. Each choice adds the party to party_not. The chip in the head removes it.
function LeaveOutParty({ parties, filters, setWith }) {
  const out = (filters.party_not || "").split(",").filter(Boolean);
  const left = parties.filter((p) => !out.includes(p.party));
  if (left.length === 0) return null;
  return (
    <label className="search-leave">
      <span className="search-leave__label">Leave out a party</span>
      <select
        className="search-sort__select search-leave__select"
        value=""
        onChange={(e) => e.target.value && setWith({ party_not: [...out, e.target.value].join(",") })}
      >
        <option value="">Choose a party</option>
        {left.map((p) => (
          <option key={p.party} value={p.party}>
            {`${p.party} · ${formatNumber(p.n)} speeches`}
          </option>
        ))}
      </select>
    </label>
  );
}
