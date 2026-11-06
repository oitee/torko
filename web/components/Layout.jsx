import { useEffect, useState } from "react";
import { Link, Outlet, ScrollRestoration } from "react-router-dom";
import SiteHeader from "./SiteHeader.jsx";

const THEMES = ["system", "light", "dark"];
const THEME_KEY = "torko-theme";

function readTheme() {
  try {
    return THEMES.includes(localStorage.getItem(THEME_KEY)) ? localStorage.getItem(THEME_KEY) : "system";
  } catch {
    return "system";
  }
}

// The frame of every page: header, page content, footer.
// The theme is "system" until the reader picks one.
export default function Layout() {
  const [theme, setTheme] = useState(readTheme);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "system") root.removeAttribute("data-theme");
    else root.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      // The browser blocks storage. The theme still works for this visit.
    }
  }, [theme]);

  return (
    <>
      <SiteHeader theme={theme} onThemeChange={setTheme} />
      <div id="main" className="container site-main" tabIndex={-1}>
        <Outlet />
      </div>
      <footer className="site-footer">
        <div className="container site-footer__inner">
          <nav className="site-footer__nav" aria-label="Footer">
            <Link to="/search">Search</Link>
            <Link to="/trends">Trends</Link>
            <Link to="/method">How Torko works</Link>
            <a href="/api/docs/">API</a>
          </nav>
          <p className="site-footer__source">
            Source: Lok Sabha debates on{" "}
            <a href="https://sansad.in/ls/debates/debates" rel="noreferrer">
              sansad.in
            </a>
            . Torko is not an official site.
          </p>
        </div>
      </footer>
      {/* A new page opens at its top. The key is the path, so a change of filters in the address does not move the page. */}
      <ScrollRestoration getKey={(location) => location.pathname} />
    </>
  );
}
