import React, { useState } from "react";
import Button from "../components/Button.jsx";
import Count from "../components/Count.jsx";
import Breadcrumb from "../components/Breadcrumb.jsx";
import SpeakerLine from "../components/SpeakerLine.jsx";
import TLDR from "../components/TLDR.jsx";
import PageAnswer from "../components/PageAnswer.jsx";
import { EmptyState, ErrorState, Loading } from "../components/States.jsx";
import Chip from "../components/Chip.jsx";

// The development page displays each shared component in every form.
// It serves as a visual reference for design and testing.
export default function DevComponents() {
  const [removed, setRemoved] = useState(false);
  const [retried, setRetried] = useState(false);

  const breadcrumbTwo = [
    { label: "Home", href: "/" },
    { label: "Debates" },
  ];

  const breadcrumbSix = [
    { label: "17th Lok Sabha", href: "/term/17" },
    { label: "Session 15", href: "/session/15" },
    { label: "12 Mar 2024", href: "/date/2024-03-12" },
    { label: "Ministry of Finance", href: "/ministry/finance" },
    { label: "Banking Regulation Bill", href: "/debate/42" },
    { label: "Speech by Mahua Moitra" },
  ];

  const identifiedSpeaker = {
    member: "Mahua Moitra",
    member_id: 1052,
    party: "AITC",
    seat: "Krishnanagar",
    printed: null,
  };

  const unidentifiedSpeaker = {
    member: null,
    member_id: null,
    party: null,
    seat: null,
    printed: "DIVISION AYES 19",
  };

  return (
    <div className="container" style={{ paddingBottom: "var(--space-14)" }}>
      <PageAnswer>Components</PageAnswer>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>PageAnswer</h2>
        <h3>PageAnswer: with Count inside</h3>
        <PageAnswer
          as="div"
          count={<Count n={41} total={1318} noun="speeches" />}
        >
          Mahua Moitra delivered
        </PageAnswer>
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>Button</h2>
        <h3>Button: primary</h3>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <Button variant="primary">Share a quote</Button>
        </div>

        <h3>Button: secondary</h3>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <Button variant="secondary">Cite this speech</Button>
        </div>

        <h3>Button: text</h3>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <Button variant="text">Read the original</Button>
        </div>

        <h3>Button: as a link (with href)</h3>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <Button href="/search" variant="primary">
            Search speeches
          </Button>
        </div>

        <h3>Button: with onClick</h3>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <Button
            variant="secondary"
            onClick={() => alert("Button clicked")}
          >
            Click me
          </Button>
        </div>
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>Count</h2>
        <h3>Count: without total</h3>
        <Count n={1318} />

        <h3>Count: with total and noun</h3>
        <Count n={41} total={1318} noun="speeches" />

        <h3>Count: with href (link)</h3>
        <Count n={41} total={1318} noun="speeches" href="/speeches" />

        <h3>Count: missing n</h3>
        <Count />
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>Breadcrumb</h2>
        <h3>Breadcrumb: 2 items</h3>
        <Breadcrumb items={breadcrumbTwo} />

        <h3>Breadcrumb: 6 items (collapses on phone)</h3>
        <Breadcrumb items={breadcrumbSix} />
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>SpeakerLine</h2>
        <h3>SpeakerLine: with a member</h3>
        <SpeakerLine speech={identifiedSpeaker} />

        <h3>SpeakerLine: with no member</h3>
        <SpeakerLine speech={unidentifiedSpeaker} />
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>TLDR</h2>
        <h3>TLDR: with text</h3>
        <TLDR text="The member urges the government to release pending rural development funds." />

        <h3>TLDR: with no text (empty)</h3>
        <div style={{ border: "1px dashed var(--hairline)", padding: "var(--space-2)" }}>
          <span className="meta">TLDR with no text renders nothing.</span>
          <TLDR text="" />
        </div>
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>States</h2>
        <h3>States: Loading</h3>
        <Loading lines={3} />

        <h3>States: ErrorState (status 404)</h3>
        <ErrorState error={{ status: 404, message: "Not found" }} />

        <h3>States: ErrorState (status 500 with retry)</h3>
        <ErrorState
          error={{
            status: 500,
            message: "The server could not answer. Try again.",
          }}
          onRetry={() => setRetried(true)}
        />
        {retried && <p className="meta">Retry handler ran.</p>}

        <h3>States: EmptyState</h3>
        <EmptyState>
          This member made no speech in the 17th Lok Sabha.
        </EmptyState>
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>Chip</h2>
        <h3>Chip: plain (label only)</h3>
        <Chip label="Rural employment" />

        <h3>Chip: with count</h3>
        <Chip label="MGNREGA" count={1323} />

        <h3>Chip: with href (link)</h3>
        <Chip label="Arrears" href="/tag/arrears" />

        <h3>Chip: selected</h3>
        <Chip label="Agriculture" selected />

        <h3>Chip: with onRemove</h3>
        {!removed ? (
          <Chip label="Selected filter" onRemove={() => setRemoved(true)} />
        ) : (
          <p className="meta">Chip was removed.</p>
        )}
      </section>
    </div>
  );
}
