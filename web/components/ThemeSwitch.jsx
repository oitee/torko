import React from "react";
import "./ThemeSwitch.css";

// The three themes, in the order the switch shows them.
// System follows the setting of the device. Light and Dark fix the theme.
export const THEME_OPTIONS = [
  { value: "system", label: "System theme" },
  { value: "light", label: "Light theme" },
  { value: "dark", label: "Dark theme" },
];

// One icon for each theme: a half-filled circle, a sun, a moon. They take the colour of the text.
function ThemeIcon({ value }) {
  const common = { width: 18, height: 18, viewBox: "0 0 24 24", "aria-hidden": "true", focusable: "false" };
  if (value === "light") {
    return (
      <svg {...common} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <circle cx="12" cy="12" r="4" />
        <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />
      </svg>
    );
  }
  if (value === "dark") {
    return (
      <svg {...common} fill="currentColor">
        <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" />
      </svg>
    );
  }
  return (
    <svg {...common}>
      <circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor" />
    </svg>
  );
}

// The ThemeSwitch component shows the three themes side by side, so the reader sees every choice at once.
// The current theme has a border. Green is not used, because green marks only actions.
export default function ThemeSwitch({ theme = "system", onChange }) {
  return (
    <div className="theme-switch" role="group" aria-label="Theme">
      {THEME_OPTIONS.map((option) => {
        const selected = option.value === theme;
        return (
          <button
            key={option.value}
            type="button"
            className={selected ? "theme-switch__option theme-switch__option--selected" : "theme-switch__option"}
            aria-label={option.label}
            aria-pressed={selected}
            title={option.label}
            onClick={() => {
              if (!selected && onChange) onChange(option.value);
            }}
          >
            <ThemeIcon value={option.value} />
          </button>
        );
      })}
    </div>
  );
}

export { ThemeSwitch };
