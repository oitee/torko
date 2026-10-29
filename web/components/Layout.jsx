import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";
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
