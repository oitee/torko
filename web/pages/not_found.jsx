import React, { useEffect } from "react";
import { useLocation } from "react-router-dom";
import Button from "../components/Button.jsx";
import SearchBox from "../components/SearchBox.jsx";
import HouseSeats from "./home/HouseSeats.jsx";
import "./home/HomeHero.css";
import "./not_found.css";

// The page for an address that has no page. The server sends this address with status 404.
export default function NotFound() {
  const { pathname } = useLocation();

  useEffect(() => {
    document.title = "Page not found · Torko";
  }, []);

  return (
    <main className="not-found">
      <section className="ink-band home-hero" aria-labelledby="not-found-title">
        <div className="home-hero__grid">
          <div className="home-hero__text">
            <h1 id="not-found-title" className="home-hero__title">
              Page not found.
            </h1>
            <p className="home-hero__lede">
              Torko has no page at <code className="not-found__path">{pathname}</code>. The link can be old, or the
              address can have an error.
            </p>
            <Button variant="primary" href="/" className="not-found__cta">
              Go to the home page
            </Button>
            <div className="not-found__search">
              <p className="not-found__search-label" id="not-found-search-label">
                Or search the debates
              </p>
              <SearchBox buttonVariant="secondary" labelledBy="not-found-search-label" />
            </div>
          </div>
          {/* The picture is decoration on this page. The text above says everything. */}
          <div aria-hidden="true">
            <HouseSeats />
          </div>
        </div>
      </section>
    </main>
  );
}
