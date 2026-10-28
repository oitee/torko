import React, { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import Breadcrumb from "../components/Breadcrumb.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import TagHead from "./tag/TagHead.jsx";
import TagTermBar from "./tag/TagTermBar.jsx";
import TagWhenChart from "./tag/TagWhenChart.jsx";
import TagPartyChart from "./tag/TagPartyChart.jsx";
import TagMembersList from "./tag/TagMembersList.jsx";
import TagRecentSpeeches from "./tag/TagRecentSpeeches.jsx";
import TagSubjectsList from "./tag/TagSubjectsList.jsx";
import TagRelatedTags from "./tag/TagRelatedTags.jsx";
import "./tag.css";

// The Tag page displays a subject tag, historical trends, speaker parties,
// top members, recent speeches, specific subjects, and related tags.
export default function Tag() {
  const { slug } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const term = searchParams.get("term") || "";

  const [tag, setTag] = useState(null);
  const [loading, setLoading] = useState(true);
  const [termLoading, setTermLoading] = useState(false);
  const [error, setError] = useState(null);

  const prevSlugRef = useRef(slug);

  const fetchTag = () => {
    const isTermOnlyChange = Boolean(tag && prevSlugRef.current === slug);
    if (isTermOnlyChange) {
      setTermLoading(true);
    } else {
      setLoading(true);
    }
    setError(null);

    const params = term ? { term } : undefined;
    getJSON(`/api/tag/${slug}`, params)
      .then((data) => {
        setTag(data);
        prevSlugRef.current = slug;
        setLoading(false);
        setTermLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
        setTermLoading(false);
      });
  };

  useEffect(() => {
    fetchTag();
  }, [slug, term]);

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

  if (loading && !tag) {
    return (
      <main className="tag-page tag-page--loading">
        <h1 className="sr-only">Tag</h1>
        <Loading lines={4} />
      </main>
    );
  }

  if (error && !tag) {
    return (
      <main className="tag-page tag-page--error">
        <ErrorState error={error} onRetry={fetchTag} />
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

  return (
    <PageLayout
      breadcrumb={<Breadcrumb items={breadcrumbItems} />}
      answer={<TagHead tag={tag} />}
    >
      <TagTermBar
        tag={tag}
        selectedTerm={term}
        onTermChange={handleTermChange}
      />

      {termLoading ? (
        <div className="tag-main tag-main--loading">
          <Loading lines={6} />
        </div>
      ) : error ? (
        <div className="tag-main tag-main--error">
          <ErrorState error={error} onRetry={fetchTag} />
        </div>
      ) : (
        <div className="tag-main">
          <TagWhenChart
            sessions={tag.sessions}
            selectedTerm={term}
          />

          <div className="tag-side-by-side">
            <TagPartyChart
              parties={tag.parties}
              selectedTerm={term}
            />
            <TagMembersList
              members={tag.members}
              selectedTerm={term}
            />
          </div>

          <TagRecentSpeeches
            speeches={tag.recent}
            slug={tag.slug || slug}
            selectedTerm={term}
          />

          <TagSubjectsList subjects={tag.subjects} />

          <TagRelatedTags related={tag.related} />

          <section className="tag-section tag-section--method">
            <HowTorkoCounts>
              A speech carries this tag when the model named it in the speech,
              when a word of the tag matched, or when the TLDR is near the tag
              in meaning. Each speech counts once. A member counts once.
            </HowTorkoCounts>
          </section>
        </div>
      )}
    </PageLayout>
  );
}
