import React, { useEffect } from "react";
import { useAnswer } from "../assets/js/useApi.js";
import PageAnswer from "../components/PageAnswer.jsx";
import PageLayout from "../components/PageLayout.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import { formatNumber } from "../assets/js/format.js";
import MethodStep from "./method/MethodStep.jsx";
import MethodLabels from "./method/MethodLabels.jsx";
import MethodLimits from "./method/MethodLimits.jsx";
import MethodCounts from "./method/MethodCounts.jsx";
import LegacyExample from "./method/LegacyExample.jsx";
import SpeechExample from "./method/SpeechExample.jsx";
import SubjectsExample from "./method/SubjectsExample.jsx";
import SubjectGroupExample from "./method/SubjectGroupExample.jsx";
import "./method.css";

const CODE_URL = "https://github.com/oitee/torko";

// The answer of the page. The three verbs are the three jobs of Torko, so they keep the full ink colour,
// and the rest of the sentence is grey. Green is not used, because green marks only actions.
function Answer() {
  return (
    <PageAnswer>
      <span className="method-answer">
        Torko <span className="method-answer__verb">reads</span> the Lok Sabha debates,{" "}
        <span className="method-answer__verb">finds</span> who spoke each turn, and{" "}
        <span className="method-answer__verb">tags</span> each speech with its subjects.
      </span>
    </PageAnswer>
  );
}

// The Method page: how Torko works, as a flow of five steps, each with a real example.
// Then what Torko gets wrong, then the totals, then the sources. Every figure and example comes from /api/method.
export default function Method() {
  const { data, error, retry } = useAnswer("/api/method");

  useEffect(() => {
    document.title = "How Torko works · Torko";
  }, []);

  if (error) {
    return (
      <PageLayout answer={<Answer />}>
        <ErrorState error={error} onRetry={retry} />
      </PageLayout>
    );
  }

  if (!data) {
    return (
      <PageLayout answer={<Answer />}>
        <Loading lines={6} />
      </PageLayout>
    );
  }

  const { corpus = {}, speeches = {} } = data;
  const examples = data.examples || {};
  const minWords = speeches.min_words ?? 50;

  return (
    <PageLayout answer={<Answer />}>
      <div className="method-page">
        <ol className="method-page__steps">
          <MethodStep
            n={1}
            title="Read the debates"
            example={<LegacyExample example={examples.legacy} />}
          >
            <p>
              Torko reads each debate page on sansad.in. Debates before about 2009 store Hindi in an old font, which
              makes the text read as gibberish. Torko converts that text to readable Hindi.
            </p>
          </MethodStep>

          <MethodStep
            n={2}
            title="Find who spoke"
            example={<MethodLabels example={data.example} />}
          >
            <p>
              sansad.in prints the name of each speaker as plain text, with no fixed pattern. Same person can be
              spelled in a number of ways - sometimes including their constituency, sometimes in Hindi, sometimes
              with a typo, sometimes all of it. Torko reads each member's name and matches it to one member.
            </p>
          </MethodStep>

          <MethodStep
            n={3}
            title="Join turns into speeches"
            example={<SpeechExample example={examples.speech} />}
          >
            <p>
              The chair and other members often interrupt a speech. Torko joins the turns of a member into one speech
              when only the chair, or other members with 25 words or fewer, speak between them.
            </p>
          </MethodStep>

          <MethodStep
            n={4}
            title="Find the subjects of each speech"
            example={<SubjectsExample example={examples.subjects} />}
          >
            <p>
              A language model reads each speech of {minWords} words or more. It writes a TLDR and names the subjects
              of the speech. A second model checks each subject against the speech. Torko keeps a subject only when
              that model is confident.
            </p>
          </MethodStep>

          <MethodStep
            n={5}
            title="Link subjects to tags"
            figure={corpus.tags != null && <>{formatNumber(corpus.tags)} tags</>}
            example={<SubjectGroupExample example={examples.subject_group} />}
            last
          >
            <p>
              Different speeches name one subject in different words. Torko joins these names into one specific
              subject, and links the subject to a tag in its own list of tags.
            </p>
          </MethodStep>
        </ol>

        <MethodLimits data={data} />

        <MethodCounts data={data} />

        <section className="method-page__sources" aria-labelledby="method-sources-title">
          <h2 id="method-sources-title" className="method-page__title">
            Sources
          </h2>
          <ul className="method-page__list">
            <li>
              Debates: the Lok Sabha debates on <a href="https://sansad.in/ls/debates/digitized" target="_blank" rel="noopener noreferrer">sansad.in</a>.
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
