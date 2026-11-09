import { useEffect, useRef, useState } from "react";
import Button from "./Button.jsx";

// CopyButton copies a text to the clipboard and says "Copied" for 2 seconds. A screen reader hears the change.
// text is a string, or a function that gives the string at the time of the click. onResult(ok) hears if the copy worked.
export default function CopyButton({ text, children = "Copy", copiedLabel = "Copied", variant = "text", className = "", onResult }) {
  const [copied, setCopied] = useState(false);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  const handleClick = async () => {
    const value = typeof text === "function" ? text() : text;
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(false), 2000);
      onResult?.(true);
    } catch {
      onResult?.(false);
    }
  };

  return (
    <Button variant={variant} onClick={handleClick} className={`copy-button ${className}`.trim()}>
      <span aria-live="polite">{copied ? copiedLabel : children}</span>
    </Button>
  );
}

// Example: "Words" - Mahua Moitra (AITC, Krishnanagar), Lok Sabha, 2025-12-17. https://torko.in/speech/178379
export function speechCitation({ quote, member, party, seat, date, id, origin = globalThis.location?.origin ?? "" }) {
  const who = [member || "Speaker not identified", [party, seat].filter(Boolean).join(", ")].filter(Boolean);
  const head = quote ? `“${quote.trim()}” - ` : "";
  const name = who.length > 1 && who[1] ? `${who[0]} (${who[1]})` : who[0];
  return `${head}${name}, Lok Sabha, ${date}. ${origin}/speech/${id}`;
}
