import React from "react";
import { Link, useLocation } from "react-router-dom";
import Logo from "./Logo.jsx";
import "./SiteHeader.css";

const THEMES = ["system", "light", "dark"];

// The SiteHeader component renders the top navigation band.
// It includes the logo, a search link, and the theme switcher.
export default function SiteHeader({
  theme = "system",
  onThemeChange,
  setTheme,
}) {
  const location = useLocation();
  const isSearchActive = location.pathname.startsWith("/search");

  const handleToggle = () => {
    const next = THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length];
    if (onThemeChange) {
      onThemeChange(next);
    } else if (setTheme) {
      setTheme(next);
    }
  };

  const themeLabel = `Theme: ${theme.charAt(0).toUpperCase() + theme.slice(1)}`;

  return (
    <header className="site-header">
      <div className="container site-header__row">
        <Logo />
        <nav aria-label="Site navigation" className="site-header__nav">
          <Link
            to="/search"
            className={
              isSearchActive
                ? "site-header__link site-header__link--active"
                : "site-header__link"
            }
            aria-current={isSearchActive ? "page" : undefined}
          >
            Search
          </Link>
          <button
            type="button"
            className="site-header__theme"
            onClick={handleToggle}
          >
            {themeLabel}
          </button>
        </nav>
      </div>
    </header>
  );
}

export { SiteHeader };
