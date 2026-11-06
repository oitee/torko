import "./tag/TagMargin.css";
import React, { useEffect } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { useApi } from "../assets/js/useApi.js";
import { getJSON } from "../assets/js/api.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import NotFound from "./not_found.jsx";
import TagHead from "./tag/TagHead.jsx";
import TagTermBar from "./tag/TagTermBar.jsx";
import TagWhenChart from "./tag/TagWhenChart.jsx";
import TagPartyChart from "./tag/TagPartyChart.jsx";
import TagMembersList from "./tag/TagMembersList.jsx";
import TagRecentSpeeches from "./tag/TagRecentSpeeches.jsx";
import TagSubjectsList from "./tag/TagSubjectsList.jsx";
import TagRelatedTags from "./tag/TagRelatedTags.jsx";
import TagMargin from "./tag/TagMargin.jsx";
import "./tag.css";

// The Tag page displays a subject tag, historical trends, speaker parties,
// top members, recent speeches, specific subjects, and related tags.
export default function Tag() {
  const { slug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const term = searchParams.get("term") || "";

  // A change of term keeps the page and reloads only the main part. A change of tag reloads the page.
  const key = `${slug}?${term || ""}`;
  const { data: tag, dataKey, loading: anyLoading, error, retry } = useApi(key, (signal) =>
    getJSON(`/api/tag/${slug}`, term ? { term } : undefined, { signal })
  );
  const termLoading = anyLoading && Boolean(dataKey?.startsWith(`${slug}?`));
  const loading = anyLoading && !termLoading;

  // Update browser tab title
  useEffect(() => {
    if (tag?.name) {
      document.title = `${tag.name} · Torko`;
    } else if (error?.status === 404) {
      document.title = "Page not found · Torko";
    }
  }, [tag, error]);

  const handleTermChange = (newTerm) => {
    const nextParams = new URLSearchParams(searchParams);
    if (!newTerm || newTerm === "all") {
      nextParams.delete("term");
    } else {
      nextParams.set("term", newTerm);
    }
    setSearchParams(nextParams);
  };

  if (loading) {
    return (
      <main className="tag-page tag-page--loading">
        <h1 className="sr-only">Tag</h1>
        <Loading lines={4} />
      </main>
    );
  }

  if (error?.status === 404 && !tag) return <NotFound />;

  if (error && !tag) {
    return (
      <main className="tag-page tag-page--error">
        <ErrorState error={error} onRetry={retry} />
      </main>
    );
  }

  if (!tag) {
    return null;
  }

  const breadcrumbItems = [
    { label: "Topics" },
    ...(tag.domain ? [{ label: tag.domain }] : []),
    { label: tag.name },
  ];

  // The speeches with the tag in the chosen terms. The party chart counts these.
  const tagSlug = tag.slug || slug;
  const termTotal = term
    ? (tag.sessions || []).filter((x) => String(x.term) === String(term)).reduce((sum, x) => sum + (Number(x.n) || 0), 0)
    : tag.total;

  return (
    <PageLayout
      breadcrumb={<Breadcrumb items={breadcrumbItems} />}
      answer={<TagHead tag={tag} />}
      notes={<TagMargin tag={{ ...tag, slug: tagSlug }} />}
    >
      <TagTermBar
        tag={tag}
        selectedTerm={term}
        onTermChange={handleTermChange}
      />

      {termLoading ? (
        <div className="page-main tag-main--loading">
          <Loading lines={6} />
        </div>
      ) : error ? (
        <div className="page-main tag-main--error">
          <ErrorState error={error} onRetry={retry} />
        </div>
      ) : (
        <div className="page-main tag-main">
          <TagWhenChart
            years={tag.years}
            slug={tagSlug}
            selectedTerm={term}
          />

          <div className="tag-side-by-side">
            <TagPartyChart
              parties={tag.parties}
              total={termTotal}
              selectedTerm={term}
            />
            <TagMembersList
              members={tag.members}
              slug={tagSlug}
              total={termTotal}
              nMembers={term ? null : tag.n_members}
              selectedTerm={term}
            />
          </div>

          <TagRecentSpeeches
            speeches={tag.recent}
            slug={tag.slug || slug}
            selectedTerm={term}
          />

          <TagSubjectsList subjects={tag.subjects} slug={tagSlug} total={tag.total} />

          <TagRelatedTags related={tag.related} total={tag.total} />
        </div>
      )}
    </PageLayout>
  );
}
