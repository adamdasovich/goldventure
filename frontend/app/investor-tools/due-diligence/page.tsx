import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import DueDiligenceClient from "./DueDiligenceClient";

export const revalidate = 3600;

/**
 * Checked against due_diligence in core/views/investor_tools.py. The important
 * distinction from the NI 43-101 Analyzer: this endpoint performs RAG hybrid
 * retrieval and returns ranked passages with NO LLM synthesis. Do not describe
 * it as generating answers.
 */
export default function DueDiligencePage() {
  return (
    <ToolPageLayout
      slug="due-diligence"
      badge="Due Diligence"
      title="Project Due-Diligence Assistant"
      intro="Ask a due-diligence question about a company and get back the exact passages from its NI 43-101 technical reports that address it, ranked by relevance — the source text itself, not a summary of it."
      tool={<DueDiligenceClient />}
      related={["ni43-101-analyzer", "resource-growth", "peer-comparison"]}
      relatedNote={
        <>
          This returns the passages; the{" "}
          <Link
            href="/investor-tools/ni43-101-analyzer"
            className="text-gold-400 hover:underline"
          >
            NI 43-101 Report Analyzer
          </Link>{" "}
          reads them and answers in prose. Use this one when you want the
          document&apos;s own words.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                A technical report is the primary source for everything material
                about a mining project, and it is long enough that nobody reads
                it end to end. The consequence is that most due diligence is
                conducted on secondary material — the corporate presentation,
                the press release, the analyst note — each of which is a
                selection made by someone with a position.
              </p>
              <p>
                This tool goes to the primary source. You ask about metallurgy,
                recovery rates, permitting risk, capital cost or anything else,
                and it returns the passages of the technical report that address
                the question, ranked by how well they match.
              </p>
              <p>
                It deliberately does not write an answer for you. What comes
                back is the report&apos;s own text, with its own hedges,
                qualifications and caveats intact — because in due diligence the
                qualifications are frequently the point, and they are exactly
                what a summary removes.
              </p>
            </>
          ),
        },
        {
          id: "how-to-read",
          heading: "How to get useful results",
          body: (
            <>
              <p>
                <strong className="text-slate-100">
                  Use the vocabulary of the report.
                </strong>{" "}
                Technical reports say &ldquo;metallurgical recovery&rdquo;
                rather than &ldquo;how much gold do they actually get
                out&rdquo;. Retrieval matches against the document&apos;s
                language, so phrasing your question in it materially improves
                what comes back.
              </p>
              <p>
                <strong className="text-slate-100">
                  Ask about one thing at a time.
                </strong>{" "}
                A question combining metallurgy, capital cost and permitting
                retrieves passages that partly match all three and fully answer
                none.
              </p>
              <p>
                <strong className="text-slate-100">
                  Read the ranking as relevance, not importance.
                </strong>{" "}
                The top passage is the closest textual match to your question.
                It is not necessarily the most significant thing the report says
                on the subject, and the fourth result is often where the caveat
                lives.
              </p>
              <p>
                Questions that consistently repay asking: what recovery rate was
                assumed and on what test work, what the cut-off grade is and
                why, what the report says about permitting status, what
                infrastructure the project depends on, and what appears in the
                risks section. That last one is the most under-read part of
                every technical report.
              </p>
            </>
          ),
        },
        {
          id: "method",
          heading: "Method and limitations",
          body: (
            <>
              <p>
                Processed technical reports are split into passages and indexed.
                A question runs a hybrid retrieval — vector similarity to catch
                meaning and keyword matching to catch exact terminology — and
                the results are ranked before being returned.{" "}
                <strong className="text-slate-100">
                  There is no language model summarising the output.
                </strong>{" "}
                What you receive is the document&apos;s text, selected and
                ordered.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    Coverage is limited to processed reports.
                  </strong>{" "}
                  Only companies whose technical reports have been ingested
                  appear in the picker. A company with no filed report cannot be
                  queried at all.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Retrieval can miss the relevant passage.
                  </strong>{" "}
                  If the report discusses your subject in wording unlike your
                  question, the matching passage may not surface. An empty or
                  weak result is not evidence the report is silent on the topic.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Tables survive extraction poorly.
                  </strong>{" "}
                  Resource tables and sensitivity analyses carry the densest
                  numbers and the most complex layout, so figures drawn from
                  them should be checked against the original document.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Passages arrive without their surrounding context.
                  </strong>{" "}
                  A sentence that reads definitively may be qualified in the
                  paragraph before or after it.
                </li>
                <li>
                  <strong className="text-slate-100">
                    The report is not neutral.
                  </strong>{" "}
                  It is prepared for the company by a qualified person, and
                  retrieving its text faithfully includes retrieving its
                  optimism.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "How is this different from the NI 43-101 Report Analyzer?",
          a: "This tool retrieves and ranks passages from the report and stops there — you read the document's own words. The Analyzer takes the same retrieved material and has Claude synthesise an answer in prose. Use this one when you want the source text with its qualifications intact; use the Analyzer when you want a direct answer to a specific question.",
        },
        {
          q: "What questions should I ask during mining due diligence?",
          a: "The ones about assumptions rather than headline outputs. What metallurgical recovery was assumed and on what test work, what cut-off grade defines the resource and why, what the permitting status actually is, what infrastructure the project depends on, what metal price the economics assume, and what the report itself lists under risks. The risks section is the most under-read part of most technical reports.",
        },
        {
          q: "Why does my question return nothing useful?",
          a: "Usually because the phrasing does not match the report's vocabulary. Technical reports use precise industry language — 'metallurgical recovery', 'strip ratio', 'cut-off grade' — and retrieval matches against that. Rephrasing in the document's terms, and asking about one topic at a time, usually fixes it.",
        },
        {
          q: "Can I rely on numbers pulled from the passages?",
          a: "Verify anything material against the original document, particularly figures from tables. Resource tables and sensitivity analyses are the hardest content to extract cleanly, and a passage can also arrive without the qualification that sits in the adjacent paragraph.",
        },
      ]}
    />
  );
}
