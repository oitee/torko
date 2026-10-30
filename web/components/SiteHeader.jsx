import React from "react";
import { Link, useLocation } from "react-router-dom";
import Logo from "./Logo.jsx";
import ThemeSwitch from "./ThemeSwitch.jsx";
import "./SiteHeader.css";

// The SiteHeader component renders the top navigation band.
// It includes the logo, the links to the Search, Your MP and Method pages, and the theme switch.
export default function SiteHeader({
  theme = "system",
  onThemeChange,
  setTheme,
}) {
  const location = useLocation();
  const isSearchActive = location.pathname.startsWith("/search");
  const isMethodActive = location.pathname.startsWith("/method");
  const isMyMpActive = location.pathname.startsWith("/my-mp");

  const handleThemeChange = (next) => {
    if (onThemeChange) {
      onThemeChange(next);
    } else if (setTheme) {
      setTheme(next);
    }
  };

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
          <Link
            to="/my-mp"
            className={
              isMyMpActive
                ? "site-header__link site-header__link--active"
                : "site-header__link"
            }
            aria-current={isMyMpActive ? "page" : undefined}
          >
            Your MP
          </Link>
          <Link
            to="/method"
            className={
              isMethodActive
                ? "site-header__link site-header__link--active"
                : "site-header__link"
            }
            aria-current={isMethodActive ? "page" : undefined}
          >
            Method
          </Link>
          <ThemeSwitch theme={theme} onChange={handleThemeChange} />
        </nav>
      </div>
    </header>
  );
}

export { SiteHeader };
