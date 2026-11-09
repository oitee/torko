import React, { useRef, useState } from "react";
import { formatDateLong } from "../assets/js/format.js";
import Button from "./Button.jsx";
import CopyButton from "./CopyButton.jsx";
import Popover from "./Popover.jsx";
import "./HeadActions.css";

// Today as "9 Nov 2026", for the "Accessed" part of a citation.
export function accessedToday(now = new Date()) {
  const iso = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  return formatDateLong(iso);
}

// Example: Mahua Moitra, 66 speeches in the Lok Sabha, 2019 to 2026. Torko, https://torko.in/member/1052. Source: sansad.in. Accessed 9 Nov 2026.
export function pageCitation({
  title,
  detail,
  origin = globalThis.location?.origin ?? "",
  path = globalThis.location?.pathname ?? "",
  today = accessedToday(),
}) {
  return `${title}, ${detail}. Torko, ${origin}${path}. Source: sansad.in. Accessed ${today}.`;
}

// Cite this page, in a popover, then Copy link.
export default function HeadActions({ citation, citeLabel = "Cite this page" }) {
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const wrapRef = useRef(null);

  return (
    <div className="head-actions" role="group" aria-label="Cite and share">
      <div ref={wrapRef} className="head-actions__cite-wrap">
        <Button variant="secondary" onClick={() => setOpen(!open)} aria-expanded={open}>
          {citeLabel}
        </Button>
        <Popover
          open={open}
          onClose={() => setOpen(false)}
          triggerRef={wrapRef}
          className="head-actions__popover"
          role="dialog"
          aria-label="Citation"
        >
          <div className="head-actions__citation">
            <p className="head-actions__citation-text">{citation}</p>
            <div>
              <CopyButton text={citation} copiedLabel="Citation copied" onResult={(ok) => setFailed(!ok)}>
                Copy citation
              </CopyButton>
            </div>
            {failed && (
              <p className="head-actions__note meta" role="status">
                The copy failed. Select the text above and copy it.
              </p>
            )}
          </div>
        </Popover>
      </div>
      <CopyButton text={() => globalThis.location?.href ?? ""} copiedLabel="Link copied">
        Copy link
      </CopyButton>
    </div>
  );
}

export { HeadActions };
