import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { getJSON } from "../assets/js/api.js";
import { termShort } from "../assets/js/format.js";
import Button from "../components/Button.jsx";
import Count from "../components/Count.jsx";
import Breadcrumb from "../components/Breadcrumb.jsx";
import SpeakerLine from "../components/SpeakerLine.jsx";
import TLDR from "../components/TLDR.jsx";
import PageAnswer from "../components/PageAnswer.jsx";
import { EmptyState, ErrorState, Loading } from "../components/States.jsx";
import Chip from "../components/Chip.jsx";
import ChipRow from "../components/ChipRow.jsx";
import SpeechRow from "../components/SpeechRow.jsx";
import SpeechList from "../components/SpeechList.jsx";
import TurnBox from "../components/TurnBox.jsx";
import Margin from "../components/Margin.jsx";
import HowTorkoCounts from "../components/HowTorkoCounts.jsx";
import SearchBox from "../components/SearchBox.jsx";
import FilterBar from "../components/FilterBar.jsx";
import Chart from "../components/Chart.jsx";
import MemberLine from "../components/MemberLine.jsx";

// The development page displays each shared component in every form.
// It serves as a visual reference for design and testing.
export default function DevComponents() {
  const [removed, setRemoved] = useState(false);
  const [retried, setRetried] = useState(false);

  // Address search parameters for filtering the real API data.
  const [searchParams] = useSearchParams();
  const filterParams = {};
  for (const key of ["term", "party", "kind", "subject", "session"]) {
    const val = searchParams.get(key);
    if (val) {
      filterParams[key] = val;
    }
  }
  const speechesFilters = { tag: "arrears", ...filterParams };

  const [speechesData, setSpeechesData] = useState(null);
  const [speechesLoading, setSpeechesLoading] = useState(true);
  const [speechesError, setSpeechesError] = useState(null);

  const [memberData, setMemberData] = useState(null);
  const [memberLoading, setMemberLoading] = useState(true);
  const [memberError, setMemberError] = useState(null);

  const filterKey = JSON.stringify(speechesFilters);

  // The total of the tag with no filter, for the form "72 of 205 speeches".
  const [tagTotal, setTagTotal] = useState(null);
  useEffect(() => {
    getJSON("/api/speeches", { tag: "arrears", per_page: 1 })
      .then((res) => setTagTotal(res.total))
      .catch(() => setTagTotal(null));
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setSpeechesLoading(true);
    setSpeechesError(null);

    getJSON(
      "/api/speeches",
      { ...speechesFilters, facets: 1, per_page: 1 },
      { signal: controller.signal }
    )
      .then((res) => {
        setSpeechesData(res);
        setSpeechesLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) {
          return;
        }
        setSpeechesError(err);
        setSpeechesLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, [filterKey]);

  useEffect(() => {
    const controller = new AbortController();
    setMemberLoading(true);
    setMemberError(null);

    getJSON("/api/member/1052", {}, { signal: controller.signal })
      .then((res) => {
        setMemberData(res);
        setMemberLoading(false);
      })
      .catch((err) => {
        if (controller.signal.aborted) {
          return;
        }
        setMemberError(err);
        setMemberLoading(false);
      });

    return () => {
      controller.abort();
    };
  }, []);

  const partyRows = (speechesData?.facets?.party || []).map((p) => ({
    label: p.party,
    n: p.n,
    colour: p.colour,
  }));

  const termRows = (speechesData?.facets?.term || []).map((t) => ({
    label: termShort(t.term),
    n: t.n,
  }));

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

  const threeTags = [
    { name: "Arrears", slug: "arrears" },
    { name: "West Bengal", slug: "west-bengal" },
    { name: "Rural employment", slug: "rural-employment" },
  ];

  const twelveTags = [
    { name: "Arrears", slug: "arrears" },
    { name: "West Bengal", slug: "west-bengal" },
    { name: "Rural employment", slug: "rural-employment" },
    { name: "Agriculture", slug: "agriculture" },
    { name: "Farmers", slug: "farmers" },
    { name: "MGNREGA", slug: "mgnrega" },
    { name: "Finance", slug: "finance" },
    { name: "Panchayat", slug: "panchayat" },
    { name: "Budget", slug: "budget" },
    { name: "Wages", slug: "wages" },
    { name: "Labour", slug: "labour" },
    { name: "Social Welfare", slug: "social-welfare" },
  ];

  const speechWithMember = {
    id: 178379,
    date: "2025-12-17",
    term: 18,
    kind_label: "Bill",
    debate: "Viksit Bharat Gurantee for Rojgar and Ajevika Mission (Gramin):VB-G RAM G Bill",
    member: "Mahua Moitra",
    member_id: 1052,
    party: "AITC",
    seat: "Krishnanagar",
    summary: "Opposes the VB-GRAM G Bill and the replacement of MGNREGA, arguing it shifts financial burdens to states and destroys the legal guarantee of rural employment.",
    // An invented sentence. Example data never puts invented words in the mouth of a real member.
    excerpt: "An invented example sentence of a speech.",
    words: 1916,
    tags: threeTags,
  };

  const speechWithoutMember = {
    id: 178380,
    date: "2025-12-17",
    term: 18,
    kind_label: "Bill",
    debate: "Viksit Bharat Gurantee for Rojgar and Ajevika Mission (Gramin):VB-G RAM G Bill",
    member: null,
    member_id: null,
    party: null,
    seat: null,
    summary: null,
    excerpt: null,
    words: 14,
    tags: [],
  };

  const turnMemberOneParaHindi = {
    seq: 1,
    kind: "member",
    member: "Om Birla",
    member_id: 225,
    text: "क्या आप सभी पीछे वाले सदस्य आज दादा के नेतृत्व में हैं? दादा से सीखिए, इस उम्र में, तबीयत खराब होने के बाद भी सदन में आते हैं और पूरे समय बैठते हैं।\n\n? (व्यवधान)",
    words: 37,
  };

  const turnMemberFourParas = {
    seq: 14,
    kind: "member",
    // An invented text, so the speaker is an invented member with no page.
    member: "Example Member",
    member_id: null,
    text: "First invented paragraph of an example turn.\n\nSecond invented paragraph.\n\nThird invented paragraph. It is hidden until the reader clicks Read more.\n\nFourth invented paragraph.",
    words: 85,
  };

  const turnPresiding = {
    seq: 5,
    kind: "presiding",
    text: "अगर सदन में तीन सौ सदस्य रहेंगे तो दस घंटे चर्चा करा दूंगा।\n\n? (व्यवधान)",
    words: 15,
  };

  const turnCrowd = {
    seq: 25,
    kind: "crowd",
    text: "Yes.",
    words: 1,
  };

  const turnUnattributed = {
    seq: 0,
    kind: "unattributed",
    text: "VB-G RAM G Bill",
    words: 4,
  };

  return (
    <div className="container" style={{ paddingBottom: "var(--space-14)" }}>
      <PageAnswer>Components</PageAnswer>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>SiteHeader</h2>
        <p className="meta">
          The SiteHeader is displayed at the top of every page.
        </p>
      </section>

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
        <div
          style={{
            border: "1px dashed var(--hairline)",
            padding: "var(--space-2)",
          }}
        >
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

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>ChipRow</h2>
        <h3>ChipRow: with 3 tags</h3>
        <ChipRow tags={threeTags} />

        <h3>ChipRow: with 12 tags (collapses at 8)</h3>
        <ChipRow tags={twelveTags} />
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>SpeechRow</h2>
        <h3>SpeechRow: with a member</h3>
        <SpeechRow speech={speechWithMember} />

        <h3>SpeechRow: with no member</h3>
        <SpeechRow speech={speechWithoutMember} />
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>TurnBox</h2>
        <h3>TurnBox: member (1 paragraph in Hindi)</h3>
        <TurnBox turn={turnMemberOneParaHindi} meta="Speech 1 of 52" />

        <h3>TurnBox: member (4 paragraphs with Read more)</h3>
        <TurnBox
          turn={turnMemberFourParas}
          meta="Speech 14 of 52"
          summary="Opposes the replacement of MGNREGA."
        />

        <h3>TurnBox: presiding (The Chair)</h3>
        <TurnBox turn={turnPresiding} meta="Interruption" />

        <h3>TurnBox: crowd (Several members)</h3>
        <TurnBox turn={turnCrowd} />

        <h3>TurnBox: unattributed</h3>
        <TurnBox turn={turnUnattributed} />
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>Margin and HowTorkoCounts</h2>
        <h3>Margin: with a short note</h3>
        <Margin>
          <HowTorkoCounts>
            A turn under 50 words is counted as a short remark.
          </HowTorkoCounts>
        </Margin>
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>SearchBox (real API)</h2>
        <SearchBox />
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>FilterBar with real facets</h2>
        <p className="meta" style={{ marginBottom: "var(--space-4)" }}>
          The FilterBar reads and writes filters in the address. SpeechList and Charts update together when you click a chip.
        </p>
        {speechesLoading ? (
          <Loading />
        ) : speechesError ? (
          <ErrorState error={speechesError} />
        ) : (
          <FilterBar
            facets={speechesData?.facets || {}}
            total={speechesData?.total || 0}
            unfilteredTotal={tagTotal}
            noun="speeches"
          />
        )}

        <h3 style={{ marginTop: "var(--space-6)" }}>
          SpeechList under FilterBar (filtered by address)
        </h3>
        <SpeechList filters={speechesFilters} />
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>Chart: parties (party colours)</h2>
        {speechesLoading ? (
          <Loading />
        ) : speechesError ? (
          <ErrorState error={speechesError} />
        ) : (
          <Chart
            title="From which party (speeches on arrears)"
            rows={partyRows}
            total={speechesData?.total}
            party={true}
          />
        )}
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>Chart: Lok Sabha terms (no party colours)</h2>
        {speechesLoading ? (
          <Loading />
        ) : speechesError ? (
          <ErrorState error={speechesError} />
        ) : (
          <Chart
            title="By Lok Sabha term (speeches on arrears)"
            rows={termRows}
            total={speechesData?.total}
            party={false}
          />
        )}
      </section>

      <section style={{ marginTop: "var(--space-8)" }}>
        <h2>MemberLine (real data: Mahua Moitra, ID 1052)</h2>
        {memberLoading ? (
          <Loading />
        ) : memberError ? (
          <ErrorState error={memberError} />
        ) : (
          <MemberLine member={memberData} />
        )}
      </section>
    </div>
  );
}
