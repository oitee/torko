import React, { useEffect, useState } from "react";
import { getJSON } from "../assets/js/api.js";
import PageAnswer from "../components/PageAnswer.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import { countOf, formatDateLong, formatNumber } from "../assets/js/format.js";
import MethodStep from "./method/MethodStep.jsx";
import MethodLabels from "./method/MethodLabels.jsx";
import MethodLimits from "./method/MethodLimits.jsx";
import "./method.css";

const CODE_URL = "https://github.com/oitee/torko";

// The Method page: how Torko works, in four steps, then what it gets wrong, then the sources.
// It is a broad outline, not a full account of each step. Every figure comes from /api/method.
export default function Method() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = () => {
    setError(null);
    getJSON("/api/method")
      .then(setData)
      .catch(setError);
  };

  useEffect(load, []);

  useEffect(() => {
    document.title = "How Torko works · Torko";
  }, []);

  const answer = (
    <PageAnswer>Torko reads the Lok Sabha debates, finds who spoke each turn, and tags each speech with its subjects.</PageAnswer>
  );

  if (error) {
    return (
      <PageLayout answer={answer}>
        <ErrorState error={error} onRetry={load} />
      </PageLayout>
    );
  }

  if (!data) {
    return (
      <PageLayout answer={answer}>
        <Loading lines={6} />
      </PageLayout>
    );
  }

  const { corpus = {}, turns = {}, speeches = {} } = data;
  // The turns of one person: all turns except those of the chair and of many members at once.
  const oneSpeaker = turns.total != null && turns.chair_or_crowd != null ? turns.total - turns.chair_or_crowd : null;

  return (
    <PageLayout answer={answer}>
      <div className="method-page">
        <ol className="method-page__steps">
          <MethodStep
            n={1}
            title="Read the debates"
            figure={
              corpus.debates != null && (
                <>
                  {formatNumber(corpus.debates)} debates, {formatDateLong(corpus.first)} to {formatDateLong(corpus.last)}
                  {turns.total != null && <> · {formatNumber(turns.total)} turns</>}
                </>
              )
            }
          >
            <p>
              Torko copies each debate page from sansad.in and keeps the original page. It reads the text of each
              turn from that page. Debates before about 2009 store Hindi in an old font. Torko converts that text to
              readable Hindi.
            </p>
          </MethodStep>

          <MethodStep
            n={2}
            title="Find who spoke"
            figure={
              turns.member != null &&
              oneSpeaker != null && (
                <>
                  {countOf(turns.member, oneSpeaker)} turns of one speaker have a member name. The count leaves out
                  the {formatNumber(turns.chair_or_crowd)} turns of the chair and of many members at once.
                </>
              )
            }
          >
            <p>
              sansad.in prints the number of a member only on the first turn of that member in a debate. Later turns
              have only a printed name, and the source prints the name of one member in many forms. Torko matches
              each printed name to one member. A member keeps one identity in all terms.
            </p>
            <p>When two members can match one name, Torko gives no name. A missing name is better than a wrong name.</p>
            <MethodLabels example={data.example} />
          </MethodStep>

          <MethodStep
            n={3}
            title="Join turns into speeches"
            figure={
              speeches.total != null && (
                <>
                  {formatNumber(speeches.total)} speeches
                  {speeches.with_member != null && (
                    <> · {countOf(speeches.with_member, speeches.total)} have a member</>
                  )}
                </>
              )
            }
          >
            <p>
              A speech is one contribution of one member. Other members often interrupt a speech for a few words.
              Torko joins the turns of a member into one speech when only short interruptions of 25 words or fewer
              come between them.
            </p>
          </MethodStep>

          <MethodStep
            n={4}
            title="Give each speech its subjects"
            figure={
              speeches.eligible != null && (
                <>
                  Of the {formatNumber(speeches.eligible)} speeches of a member with {speeches.min_words} words or
                  more, {formatNumber(speeches.with_tldr)} have a TLDR and {formatNumber(speeches.with_tag)} have at
                  least one tag
                  {corpus.tags != null && <> · {formatNumber(corpus.tags)} tags</>}
                </>
              )
            }
          >
            <p>
              A language model reads each speech of {speeches.min_words ?? 50} words or more. It writes a TLDR and lists
              the subjects of the speech. A second model checks each subject against the speech. Torko keeps a
              subject only when that model is confident.
            </p>
            <p>
              Torko then links each subject to a tag in its own list of tags. A broad tag holds its more specific
              subjects. For example, the tag Arrears holds the wage arrears of workers and the arrears of sugarcane
              farmers.
            </p>
          </MethodStep>
        </ol>

        <MethodLimits data={data} />

        <section className="method-page__sources" aria-labelledby="method-sources-title">
          <h2 id="method-sources-title" className="method-page__title">
            Sources
          </h2>
          <ul className="method-page__list">
            <li>
              Debates: the Lok Sabha debates on <a href="https://sansad.in/ls/debates/digitized">sansad.in</a>.
            </li>
            <li>
              The party of each member on each date: sansad.in, the Wikipedia lists of the members of each term, and a
              manual review.
            </li>
            <li>
              The code of Torko: <a href={CODE_URL}>github.com/oitee/torko</a>.
            </li>
          </ul>
        </section>
      </div>
    </PageLayout>
  );
}
