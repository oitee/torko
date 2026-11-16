import React, { useEffect } from "react";
import { useAnswer } from "../assets/js/useApi.js";
import { ErrorState } from "../components/States.jsx";
import HomeHero from "./home/HomeHero.jsx";
import HomeMethod from "./home/HomeMethod.jsx";
import HomeRising from "./home/HomeRising.jsx";
import HomeMember from "./home/HomeMember.jsx";
import HomeQuote from "./home/HomeQuote.jsx";
import HomeTrend from "./home/HomeTrend.jsx";
import "./home.css";

// The Home page. It reads one answer, /api/home. The server sends it from a file that the rebuild writes.
// The top band holds the search and the site figures (corpus).
// The parts below show what Torko can do: the hand-checked sample (featured) and the counts of each step (method).
// The search box shows also when the answer fails.
export default function Home() {
  const home = useAnswer("/api/home");

  useEffect(() => {
    document.title = "Torko · Lok Sabha debates";
  }, []);

  const f = home.data?.featured;

  return (
    <main className="home-page">
      <HomeHero
        corpus={home.data?.corpus}
        corpusError={home.error}
        onRetryCorpus={home.retry}
        ideas={f?.search_ideas}
      />

      <section className="home-main" aria-label="More on Torko">
        {home.data && (
          <HomeRising
            typical={home.data.typical}
            sessionLabel={home.data.session_label}
            term={home.data.term}
          />
        )}

        <section className="home-can-do" aria-labelledby="home-can-do">
          <h2 id="home-can-do" className="home-can-do__title">
            What you can do
          </h2>
          <div className="home-can-do__list">
            {home.loading ? (
              <FeaturedSkeleton />
            ) : home.error ? (
              <ErrorState error={home.error} onRetry={home.retry} />
            ) : f ? (
              <>
                <HomeMember member={f.member} />
                <HomeQuote quote={f.quote} />
                <HomeTrend trend={f.trend} />
              </>
            ) : null}

            <HomeMethod method={home.data?.method} loading={home.loading} />
          </div>
        </section>
      </section>
    </main>
  );
}

// Three grey blocks of a fixed height, while the examples load. The page does not jump when they arrive.
function FeaturedSkeleton() {
  return (
    <div className="home-skeleton" role="status" aria-busy="true">
      <span className="home-skeleton__sr-only">Loading</span>
      {[0, 1, 2].map((i) => (
        <div key={i} className="home-skeleton__block" aria-hidden="true" />
      ))}
    </div>
  );
}
