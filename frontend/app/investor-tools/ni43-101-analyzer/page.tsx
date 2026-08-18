import Link from "next/link";
import ChatInterface from "@/components/ChatInterface";
import ToolPageLayout from "../ToolPageLayout";

export const revalidate = 3600;

const EXAMPLE_QUERIES = [
  "Summarize the most recent NI 43-101 report for Aston Bay",
  "What are the resource estimates in the latest technical report?",
  "Compare the NPV from the PEA against the current market cap",
  "Extract the sensitivity table from the feasibility study",
  "What are the key risks identified in the technical report?",
  "What gold price assumption was used in the economic study?",
];

/**
 * No "use client" needed here — ChatInterface carries its own client
 * boundary, so the whole page renders on the server. It previously declared
 * "use client" without using a single hook, which pushed 86 words of
 * indexable content behind a client render for no reason.
 */
export default function NI43101AnalyzerPage() {
  return (
    <ToolPageLayout
      slug="ni43-101-analyzer"
      badge="AI-Powered"
      title="NI 43-101 Report Analyzer"
      intro="Ask a question about any technical report in the database and get an answer drawn from the report itself, with the source passages attached — rather than reading three hundred pages to find one number."
      tool={
        <>
          <section className="px-4 sm:px-6 lg:px-8 pb-4">
            <div className="max-w-4xl mx-auto">
              <p className="text-xs text-slate-500 mb-2 text-center">
                Try asking:
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {EXAMPLE_QUERIES.map((q) => (
                  <span
                    key={q}
                    className="text-xs px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700/50 text-slate-400"
                  >
                    {q}
                  </span>
                ))}
              </div>
            </div>
          </section>

          <section className="py-6 px-4 sm:px-6 lg:px-8">
            <div className="max-w-4xl mx-auto">
              <ChatInterface />
            </div>
          </section>
        </>
      }
      related={["due-diligence", "peer-comparison", "resource-growth"]}
      relatedNote={
        <>
          For a structured walk through the document itself, start with{" "}
          <Link
            href="/guides/how-to-read-ni-43-101-report"
            className="text-gold-400 hover:underline"
          >
            our guide to reading an NI 43-101 report
          </Link>{" "}
          — the five sections that matter, the resource categories, and ten red
          flags that mark a weak report.
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                An NI 43-101 technical report is the most authoritative document
                a mining company produces and the least likely to be read. They
                run to hundreds of pages, they are written by geologists for
                regulators, and the handful of numbers an investor actually
                wants — the resource table, the NPV, the metal price assumption,
                the capital cost — are buried at unpredictable depths.
              </p>
              <p>
                The result is that most investors rely on the company&apos;s own
                summary of its own report. That summary is accurate, in the
                narrow sense that it does not contain falsehoods, and it is also
                written by people with an interest in which figures you notice.
              </p>
              <p>
                This tool lets you interrogate the report directly. Ask a
                specific question and get an answer assembled from the relevant
                passages, with the source material shown, so you can check what
                the report says rather than what the press release said it says.
              </p>
            </>
          ),
        },
        {
          id: "how-to-read",
          heading: "How to get useful answers",
          body: (
            <>
              <p>
                <strong className="text-slate-100">
                  Ask narrow questions.
                </strong>{" "}
                &ldquo;What gold price did the PEA assume?&rdquo; retrieves
                cleanly. &ldquo;Is this a good project?&rdquo; does not, because
                there is no passage in the report that answers it.
              </p>
              <p>
                <strong className="text-slate-100">
                  Name the company and the report.
                </strong>{" "}
                Many companies have several technical reports across several
                projects and several years. Specifying which one you mean avoids
                answers assembled from the wrong document.
              </p>
              <p>
                <strong className="text-slate-100">
                  Ask for the assumptions, not just the outputs.
                </strong>{" "}
                An NPV is a function of the metal price, discount rate, capital
                cost and recovery assumed. The headline figure is far less
                informative than the inputs that produced it, and the inputs are
                what you should be testing.
              </p>
              <p>
                <strong className="text-slate-100">
                  Read the cited passages.
                </strong>{" "}
                The answer points at the source text. For anything you intend to
                act on, read the passage rather than the summary of it.
              </p>
              <p>
                Questions that reliably repay asking: what cut-off grade was
                used, what recovery rate was assumed, what the sensitivity table
                shows at a lower metal price, what proportion of the resource is
                inferred, and what the report lists under risks.
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
                Technical reports are processed into text, split into passages
                and indexed. A question triggers a hybrid retrieval — vector
                similarity for meaning, keyword matching for exact terms, then
                re-ranking to order what was found. The best-matching passages
                are passed to Claude as context, and the answer is generated
                from them rather than from the model&apos;s own knowledge.
              </p>
              <p>The limits worth knowing:</p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    It can only answer from reports that have been processed.
                  </strong>{" "}
                  If a company&apos;s report is not in the database, the answer
                  will be thin or absent. Coverage is not universal.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Tables are the hardest thing to extract reliably.
                  </strong>{" "}
                  Resource tables and sensitivity analyses carry the densest
                  information and the most complex layout, so figures pulled
                  from them are the most worth verifying against the original.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Retrieval can miss.
                  </strong>{" "}
                  If the relevant passage is not among those retrieved, the
                  answer is built from incomplete context. A confidently worded
                  answer is not evidence that the right passage was found.
                </li>
                <li>
                  <strong className="text-slate-100">
                    It reports what the document says, not whether it is right.
                  </strong>{" "}
                  A technical report is prepared for the company by a qualified
                  person. This tool will faithfully relay an optimistic
                  assumption without flagging it as optimistic.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Verify anything you intend to act on.
                  </strong>{" "}
                  Treat the output as a fast route to the relevant page, not as
                  a substitute for reading it.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "What is an NI 43-101 report?",
          a: "Canada's National Instrument 43-101 is the standard governing how mining companies disclose technical information about mineral projects. A technical report prepared under it must be authored by a qualified person and covers geology, drilling, sampling, resource estimation and, where applicable, the economic study. It is the document that turns a company's claims about its deposit into something with professional accountability attached.",
        },
        {
          q: "Can it answer questions about any mining company?",
          a: "Only those whose technical reports have been processed into the database. Coverage is not universal, and a company with no filed technical report — which includes many early-stage explorers — has nothing for the tool to read.",
        },
        {
          q: "How accurate are figures pulled from resource tables?",
          a: "Tables are the hardest part of a technical report to extract reliably, because the information is dense and the layout complex. Figures drawn from resource tables and sensitivity analyses are the ones most worth checking against the original document before you rely on them.",
        },
        {
          q: "Which questions are most worth asking?",
          a: "The ones about assumptions rather than outputs. What metal price the economic study assumed, what discount rate produced the NPV, what cut-off grade defined the resource, what recovery rate was modelled, what proportion of the resource is inferred, and what the report itself lists under risks. The headline NPV is a consequence of those inputs, and the inputs are where the judgement lives.",
        },
        {
          q: "Does the tool tell me whether a project is good?",
          a: "No. It reports what the document says. A technical report is prepared for the company, and an optimistic metal price assumption will be relayed as faithfully as a conservative one. Judging whether the assumptions are reasonable is the part that remains yours.",
        },
      ]}
    />
  );
}
