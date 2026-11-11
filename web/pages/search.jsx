import React, { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { useApi } from "../assets/js/useApi.js";
import { formatNumber, termShort } from "../assets/js/format.js";
import Button from "../components/Button.jsx";
import Breadcrumb from "../components/Breadcrumb.jsx";
import Chip from "../components/Chip.jsx";
import Count from "../components/Count.jsx";
import PageLayout from "../components/PageLayout.jsx";
import SearchBox from "../components/SearchBox.jsx";
import SearchMatches from "./search/SearchMatches.jsx";
import SearchResults from "./search/SearchResults.jsx";
import SearchScopeCard from "./search/SearchScopeCard.jsx";
import SearchSuggested from "./search/SearchSuggested.jsx";
import FilterRail from "./search/FilterRail.jsx";
import CopyButton from "../components/CopyButton.jsx";
import SearchLanding from "./search/SearchLanding.jsx";
import { chipsFrom, draftChanges, draftFrom, listOf } from "./search/filterRules.js";
import { FILTER_KEYS, defaultSort, headingParts, readSearch } from "./search/searchParams.js";
import "./search.css";

const PER_PAGE = 20;

// Where the name of a scope comes from, for the heading and the scope chip.
const SCOPE_NAME_URL = {
  tag: (v) => `/api/tag/${encodeURIComponent(v)}`,
  place: (v) => `/api/place/${encodeURIComponent(v)}`,
  member: (v) => `/api/member/${encodeURIComponent(v)}`,
};

// The Search page: the speeches that contain the words, the pages whose names match, and filters.
export default function Search() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { scope, filters, view, sort, page } = readSearch(searchParams);
  const params = { ...scope, ...filters };
  const q = scope.q || "";
  const hasFilters = Object.keys(params).some((k) => k !== "q");
  const searched = Object.keys(params).length > 0;

  const listParams = { ...scope, ...filters, sort, page, per_page: PER_PAGE };
  const listKey = JSON.stringify({ listParams, view });
  const list = useApi(listKey, (signal) =>
    getJSON("/api/speeches", { ...listParams, ...(view === "members" ? { group: "member" } : {}) }, { signal })
  );
  // The other calls wait for the list. The list stores the vector and the nearest speeches of a new search for them.
  const listDone = !list.loading;

  // The landing view shows while nothing is searched. A search that starts from it keeps the landing view
  // until its results arrive, so the page changes once, from the box to the results. A direct link to a search
  // opens the results view at once.
  const resultsReady = list.dataKey === listKey && !list.loading;
  const landingRef = useRef(!searched);
  if (!searched) landingRef.current = true;
  else if (landingRef.current && (resultsReady || list.error)) landingRef.current = false;
  const landing = landingRef.current;

  // The facets are a call of their own, so the speeches do not wait for them.
  const facetParams = { ...scope, ...filters, facets: 1, per_page: 1 };
  const facetCall = useApi(listDone ? JSON.stringify(facetParams) : null, (signal) =>
    getJSON("/api/speeches", facetParams, { signal })
  );
  const speechData = view === "members" ? facetCall.data : list.data;

  // The total with no filter, for "N of total".
  const baseParams = q ? { q } : {};
  const baseKey = hasFilters ? `base:${q}` : null;
  const base = useApi(listDone ? baseKey : null, (signal) => getJSON("/api/speeches", { ...baseParams, per_page: 1 }, { signal }));

  // The tag counts are a call of their own, because they take the longest.
  const tagFacetParams = { ...params, facets: "tag", per_page: 1 };
  const tagCall = useApi(listDone ? JSON.stringify(tagFacetParams) : null, (signal) => getJSON("/api/speeches", tagFacetParams, { signal }));

  // The ticks and the date sliders of the left panel wait here until Apply. A new address starts them again.
  const draftKey = JSON.stringify([params.tag, params.party, params.term, params.date_from, params.date_to]);
  const [draft, setDraft] = useState(() => draftFrom(params));
  useEffect(() => setDraft(draftFrom(params)), [draftKey]);

  // The number of members, for the toggle. It is a separate call, so the speeches do not wait for it.
  const membersParams = { ...scope, ...filters, group: "member", per_page: 1 };
  const membersCall = useApi(view === "speeches" && listDone ? JSON.stringify(membersParams) : null, (signal) =>
    getJSON("/api/speeches", membersParams, { signal })
  );

  // The start block reads two more answers: the years and members of the whole archive, and the member with the most speeches.
  const homeCall = useApi(landing ? "start:home" : null, (signal) => getJSON("/api/home", undefined, { signal }));

  const matches = useApi(q || null, (signal) => getJSON("/api/search", { q }, { signal }));
  // The tag, place and member each load their own name, so that they can be on at the same time.
  const useScope = (k) =>
    useApi(scope[k] ? `${k}:${scope[k]}` : null, (signal) => Promise.all(listOf(scope[k]).map((v) => getJSON(SCOPE_NAME_URL[k](v), undefined, { signal }))));
  const tags = (scope.tag || "").split(",").filter(Boolean);
  // A search can hold two or more tags, so the tag answer is a list with one answer for each tag.
  const tagInfo = useApi(tags.length ? `tags:${scope.tag}` : null, (signal) =>
    Promise.all(tags.map((t) => getJSON(SCOPE_NAME_URL.tag(t), undefined, { signal })))
  );
  const scopeInfo = { place: useScope("place"), member: useScope("member") };
  // The places and tags whose whole name is in the words get the same card as a search inside them. /api/search picks them.
  const named = (matches.data?.named || []).filter((p) => !listOf(scope[p.kind]).includes(p.slug));
  const namedKey = named.length ? `named:${named.map((p) => `${p.kind}:${p.slug}`).join(",")}` : null;
  const namedInfo = useApi(namedKey, (signal) => Promise.all(named.map((p) => getJSON(SCOPE_NAME_URL[p.kind](p.slug), undefined, { signal }))));
  const scopeNames = {
    tag: tagInfo.data ? tagInfo.data.map((t) => t.name).join(" and ") : null,
    place: scopeInfo.place.data ? scopeInfo.place.data.map((t) => t.name).join(" or ") : null,
    member: scopeInfo.member.data
      ? scopeInfo.member.data.map((t) => t.name).join(" or ")
      : listOf(scope.member).map((v) => list.data?.names?.member?.[v]).filter(Boolean).join(" or ") || null,
  };

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
  // The waiting ticks go with every search that the panel starts: Apply, Add, and the removal of a chip.
  const commit = (changes = {}) => setWith({ ...draftChanges(draft), ...changes });
  const resetFilters = () => setWith(Object.fromEntries([...FILTER_KEYS, "tag", "member", "place"].map((k) => [k, null])));

  const facets = facetCall.data?.facets || {};
  const names = {
    ...(list.data?.names || {}),
    kind: Object.fromEntries((facets.kind || []).map((r) => [r.kind, r.label])),
    session: Object.fromEntries((facets.session || []).map((r) => [`${r.term}-${r.session}`, r.label || `${termShort(r.term)} session ${r.session}`])),
  };
  const chips = chipsFrom(params, names);

  const heading = headingParts({ scope, count: speechTotal, members: view === "members" ? membersTotal : null });

  // The breadcrumb names the scope of the search. With no scope to name, the page has no breadcrumb.
  const crumbLabel = q || scopeNames.tag || scopeNames.place || scopeNames.member || "";

  const answer = (
    <div className="search-head">
      <h1 className="search-head__title">
        {heading.lead !== null && <span className="search-head__count">{formatNumber(heading.lead)}</span>}
        {heading.rest}
      </h1>
      <div className="search-head__box">
        <SearchBox key={q} initial={q} />
      </div>
      {q && matches.data && (
        <SearchSuggested
          items={(matches.data.suggested || []).filter((p) => !listOf(scope[p.kind]).includes(p.slug))}
          hrefFor={(p) => hrefWith({ [p.kind]: [...listOf(scope[p.kind]), p.slug].join(",") })}
        />
      )}
      {chips.length > 0 && (
        <div className="search-head__active" aria-label="Filters that are on">
          {chips.map((c) => (
            <Chip key={c.key} label={c.label} negative={c.negative} onRemove={() => commit(c.remove)} />
          ))}
          <Button variant="secondary" onClick={resetFilters}>Reset filters</Button>
        </div>
      )}
      <div className="search-head__summary">
        {speechTotal !== null && <Count n={speechTotal} total={hasFilters ? unfilteredTotal ?? undefined : undefined} noun={searched ? "speeches" : "speeches in total"} />}
        {searched && <CopyButton text={() => window.location.href}>Copy link</CopyButton>}
      </div>
    </div>
  );

  if (landing) {
    return (
      <main className="search-page search-page--landing">
        <SearchLanding
          initial={q}
          total={searched ? null : speechTotal}
          members={homeCall.data?.corpus?.members}
          first={homeCall.data?.corpus?.first}
          last={homeCall.data?.corpus?.last}
          busy={searched}
        />
        {!searched && (
          <section id="latest-speeches" className="search-latest" aria-label="Latest speeches">
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
              memberHref={(id) => hrefWith({ member: id, view: null })}
              onSort={(s) => setWith({ sort: s === defaultSort(q) ? null : s })}
              query=""
              tagCount={0}
              heading="Latest speeches"
              hasFilters={false}
              onReset={resetFilters}
            />
          </section>
        )}
      </main>
    );
  }

  return (
    <PageLayout breadcrumb={crumbLabel ? <Breadcrumb items={[{ label: "Search", href: "/search" }, { label: crumbLabel }]} /> : null} answer={answer}>
      <div className="search-body">
        <aside className="search-rail" aria-label="Filters and method">
          <FilterRail
            params={params}
            facets={facets}
            tagRows={tagCall.data?.facets?.tag}
            names={names}
            chipCount={chips.length}
            draft={draft}
            setDraft={setDraft}
            onApply={() => commit()}
            onDiscard={() => setDraft(draftFrom(params))}
            onAdd={commit}
          />
        </aside>

        <div className="search-main">
          {namedKey && namedInfo.dataKey === namedKey && namedInfo.data && (
            <div className="search-scopes search-scopes--named">
              {named.map((p, i) => (
                <SearchScopeCard key={`${p.kind}:${p.slug}`} kind={p.kind} value={p.slug} info={namedInfo.data[i]} />
              ))}
            </div>
          )}
          {(tags.length > 0 || scope.place) && (
            <div className="search-scopes">
              {tags.map((t, i) => (
                <SearchScopeCard key={t} kind="tag" value={t} info={tagInfo.data?.[i]} />
              ))}
              {listOf(scope.place).map((v, i) => (
                <SearchScopeCard key={v} kind="place" value={v} info={scopeInfo.place.data?.[i]} />
              ))}
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
            onSort={(s) => setWith({ sort: s === defaultSort(q) ? null : s })}
            query={q}
            tagCount={tags.length}
            heading={searched ? "" : "Latest speeches"}
            hasFilters={hasFilters}
            onReset={resetFilters}
          />
        </div>
      </div>
    </PageLayout>
  );
}
