import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router-dom";

const THEMES = ["system", "light", "dark"];
const THEME_KEY = "torko-theme";

function readTheme() {
  try {
    return THEMES.includes(localStorage.getItem(THEME_KEY)) ? localStorage.getItem(THEME_KEY) : "system";
  } catch {
    return "system";
  }
}

// The frame of every page: header, page content, footer. The theme is "system" until the reader picks one.
// The header here is a first form. The SiteHeader component replaces it.
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

  const next = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
  return (
    <>
      <header className="site-header">
        <div className="container site-header__row">
          <Link to="/" className="site-header__logo">torko</Link>
          <button type="button" className="site-header__theme" onClick={() => setTheme(next)}>
            Theme: {theme[0].toUpperCase() + theme.slice(1)}
          </button>
        </div>
      </header>
      <div className="container">
        <Outlet />
      </div>
      <footer className="site-footer">
        <div className="container">
          Source: Lok Sabha debates on sansad.in. Torko is not an official site.
        </div>
      </footer>
    </>
  );
}
