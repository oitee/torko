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

// TODO before deployment: build the Data and API page.
// Then add a "Download the data" task to the Home page.
// The header shows only the pages that exist, so it gets the Data and API link then.

// The Home page. The top band holds the search and the site figures from /api/home.
// The parts below show what Torko can do, with the hand-checked sample from /api/home/featured.
// The three answers load apart, so a failed answer hides only its own parts.
export default function Home() {
  const home = useAnswer("/api/home");
  const featured = useAnswer("/api/home/featured");
  const method = useAnswer("/api/method");

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

      <section className="home-main" aria-label="More on Torko">
        {home.data && (
          <HomeRising
            typical={home.data.typical}
            session={home.data.session}
            term={home.data.term}
            first={home.data.first}
            last={home.data.last}
          />
        )}

        <section className="home-can-do" aria-labelledby="home-can-do">
          <h2 id="home-can-do" className="home-can-do__title">
            What you can do
          </h2>
          <div className="home-can-do__list">
            {featured.loading ? (
              <FeaturedSkeleton />
            ) : featured.error ? (
              <ErrorState error={featured.error} onRetry={featured.retry} />
            ) : (
              <>
                <HomeMember member={f.member} />
                <HomeQuote quote={f.quote} />
                <HomeTrend trend={f.trend} />
              </>
            )}

            <HomeMethod method={method.data} loading={method.loading} />
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
