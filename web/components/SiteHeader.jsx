import React, { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import Logo from "./Logo.jsx";
import ThemeSwitch from "./ThemeSwitch.jsx";
import "./SiteHeader.css";

// The main pages, in the order of the header. Each item is active on its path and on the paths under it.
export const NAV_ITEMS = [
  { to: "/search", label: "Search" },
  { to: "/my-mp", label: "Your MP" },
  { to: "/trends", label: "Trends" },
  { to: "/method", label: "Method" },
];

function NavLinks({ pathname, onPick }) {
  return NAV_ITEMS.map((item) => {
    const active = pathname.startsWith(item.to);
    return (
      <Link
        key={item.to}
        to={item.to}
        className={active ? "site-header__link site-header__link--active" : "site-header__link"}
        aria-current={active ? "page" : undefined}
        onClick={onPick}
      >
        {item.label}
      </Link>
    );
  });
}

// The SiteHeader component renders the top navigation band: the logo, the main pages and the theme switch.
// On a phone the links do not fit in one row. A Menu button then opens them as a list under the band.
export default function SiteHeader({ theme = "system", onThemeChange, setTheme }) {
  const { pathname } = useLocation();
  const [menuOpen, setMenuOpen] = useState(false);

  // A new page closes the menu.
  useEffect(() => setMenuOpen(false), [pathname]);

  const handleThemeChange = (next) => {
    if (onThemeChange) onThemeChange(next);
    else if (setTheme) setTheme(next);
  };

  return (
    <header className="site-header">
      <a className="site-header__skip" href="#main">
        Skip to the content
      </a>
      <div className="container site-header__row">
        <Logo />
        <nav aria-label="Site navigation" className="site-header__nav">
          <span className="site-header__wide">
            <NavLinks pathname={pathname} />
          </span>
          <button
            type="button"
            className="site-header__link site-header__menu-button"
            aria-expanded={menuOpen}
            aria-controls="site-menu"
            onClick={() => setMenuOpen((open) => !open)}
          >
            {menuOpen ? "Close" : "Menu"}
          </button>
          <ThemeSwitch theme={theme} onChange={handleThemeChange} />
        </nav>
      </div>
      {menuOpen && (
        <nav id="site-menu" aria-label="Menu" className="site-header__menu">
          <div className="container">
            <NavLinks pathname={pathname} onPick={() => setMenuOpen(false)} />
          </div>
        </nav>
      )}
    </header>
  );
}

export { SiteHeader };
