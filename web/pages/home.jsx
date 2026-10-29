import React, { useEffect, useState } from "react";
import { getJSON } from "../assets/js/api.js";
import { ErrorState, Loading } from "../components/States.jsx";
import HomeHero from "./home/HomeHero.jsx";
import HomeMember from "./home/HomeMember.jsx";
import HomeQuote from "./home/HomeQuote.jsx";
import HomeTrend from "./home/HomeTrend.jsx";
import "./home.css";

// TODO before deployment: build the Method page, the Your MP page and the Data and API page.
// Then add the parts of this page that need them:
// the "How Torko works" link, and the "Start here" list of tasks ("Find your MP", "Download the data").
// The header shows only the pages that exist, so it gets the same links then.

// Load one API answer. A page can retry it.
function useAnswer(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  const load = () => {
    setState({ data: null, error: null, loading: true });
    getJSON(path)
      .then((data) => setState({ data, error: null, loading: false }))
      .catch((error) => setState({ data: null, error, loading: false }));
  };

  useEffect(load, [path]);
  return { ...state, retry: load };
}

// The Home page. The top band holds the search and the site figures from /api/home.
// The parts below show what Torko can do, with the hand-checked sample from /api/home/featured.
// The two answers load apart, so a failed answer hides only its own parts.
export default function Home() {
  const home = useAnswer("/api/home");
  const featured = useAnswer("/api/home/featured");

  useEffect(() => {
    document.title = "Torko · Lok Sabha debates";
  }, []);

  const f = featured.data;

  return (
    <main className="home-page">
      <HomeHero
        corpus={home.data?.corpus}
        corpusError={home.error}
        onRetryCorpus={home.retry}
        ideas={f?.search_ideas}
      />

      <section className="home-main" aria-labelledby="home-can-do">
        <h2 id="home-can-do" className="home-main__title">
          What you can do
        </h2>
        {featured.loading ? (
          <Loading lines={6} />
        ) : featured.error ? (
          <ErrorState error={featured.error} onRetry={featured.retry} />
        ) : (
          <>
            <HomeMember member={f.member} />
            <HomeQuote quote={f.quote} />
            <HomeTrend trend={f.trend} />
          </>
        )}
      </section>
    </main>
  );
}
