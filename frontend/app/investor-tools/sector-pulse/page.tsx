import Link from "next/link";
import ToolPageLayout from "../ToolPageLayout";
import SectorPulseClient from "./SectorPulseClient";

export const revalidate = 3600;

/**
 * The Chrome wrapper added during the soft-404 fix is gone — ToolPageLayout
 * now supplies the nav and header, so the client renders only the dashboard.
 */
export default function SectorPulsePage() {
  return (
    <ToolPageLayout
      slug="sector-pulse"
      badge="Dashboard"
      title="Sector Pulse Dashboard"
      intro="A single view of the junior mining sector: metals prices, market breadth, the day's biggest movers, financing activity and news volume — free to use, no account required."
      tool={<SectorPulseClient />}
      related={["financing-flow", "unusual-activity", "catalyst-calendar"]}
      relatedNote={
        <>
          For the metals themselves in more detail, see{" "}
          <Link href="/metals" className="text-gold-400 hover:underline">
            live metals prices
          </Link>
          , and for the companies behind the moves,{" "}
          <Link href="/companies" className="text-gold-400 hover:underline">
            browse the directory
          </Link>
          .
        </>
      }
      sections={[
        {
          id: "what-it-does",
          heading: "What this tool does",
          body: (
            <>
              <p>
                Junior mining is a sentiment-driven sector. Individual companies
                rise and fall on their own results, but the tide underneath them
                — whether capital is flowing in, whether metals are strong,
                whether anyone is paying attention — determines most of what
                happens to most of them in any given month.
              </p>
              <p>
                That tide is normally assembled by hand from half a dozen
                sources: a metals price site, an exchange screener, a news feed,
                somewhere to see financings. This dashboard puts them in one
                place and refreshes automatically.
              </p>
              <p>
                It is one of the two tools available without an account,
                deliberately, because it is the orientation layer. Everything
                else on the platform is easier to use once you know what the
                sector is doing.
              </p>
            </>
          ),
        },
        {
          id: "how-to-read",
          heading: "How to read the dashboard",
          body: (
            <>
              <p>
                <strong className="text-slate-100">Metals prices</strong> set
                the backdrop. Junior valuations key off the underlying commodity
                with a lag, and a sustained move in the metal usually shows up
                in the explorers well after it shows up in the producers.
              </p>
              <p>
                <strong className="text-slate-100">Market breadth</strong> — how
                many companies rose versus fell — is the most useful single
                number here. A day where the metal is up but breadth is negative
                describes a sector where money is concentrating in a few names
                rather than lifting everything, which is a very different market
                from a broad rally.
              </p>
              <p>
                <strong className="text-slate-100">Top movers</strong> are
                usually reacting to something specific. A name at the top of the
                list is worth checking against its news, and if there is none,
                against the{" "}
                <Link
                  href="/investor-tools/unusual-activity"
                  className="text-gold-400 hover:underline"
                >
                  Unusual Activity Detector
                </Link>
                .
              </p>
              <p>
                <strong className="text-slate-100">Financing activity</strong>{" "}
                indicates whether the capital window is open. It is the slowest
                of these signals to move and the most consequential when it
                does.
              </p>
              <p>
                <strong className="text-slate-100">News volume</strong> tracks
                how much the sector is communicating. Sustained high volume
                usually accompanies drilling season and rising interest.
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
                Metals prices are scraped on a schedule, company prices and
                volumes come from exchange market data updated after each close,
                and financing and news figures are computed from the same
                records that drive the rest of the platform. The dashboard
                refreshes itself every five minutes.
              </p>
              <ul className="list-disc pl-6 flex flex-col gap-3">
                <li>
                  <strong className="text-slate-100">
                    Company prices are end-of-day, not live.
                  </strong>{" "}
                  Stock figures update after the close rather than intraday, so
                  the movers list describes the last completed session.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Breadth is distorted by illiquidity.
                  </strong>{" "}
                  A great many tracked listings barely trade, so a stock showing
                  no change may simply not have traded rather than having held
                  its price.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Percentage movers favour the smallest companies.
                  </strong>{" "}
                  On a stock priced at two cents, a one-cent move is 50%. The
                  top of the movers list is frequently dominated by names where
                  very little money actually changed hands.
                </li>
                <li>
                  <strong className="text-slate-100">
                    Coverage is the companies we track,
                  </strong>{" "}
                  not the entire sector, so breadth describes this universe
                  rather than every listed junior.
                </li>
              </ul>
            </>
          ),
        },
      ]}
      faqs={[
        {
          q: "Is the Sector Pulse Dashboard free?",
          a: "Yes. It is one of two tools available without an account, alongside the Resource Grade Ranker, because it is the orientation layer that makes the rest of the platform easier to use.",
        },
        {
          q: "What does market breadth tell me?",
          a: "Whether a move is broad or narrow. If the metal is up and most companies are up with it, capital is flowing into the sector generally. If the metal is up while more companies fall than rise, money is concentrating into a handful of favoured names — a much less healthy market, and one where index-level optimism does not reach most holdings.",
        },
        {
          q: "Why are the top movers usually tiny companies?",
          a: "Because percentage moves scale inversely with share price. On a two-cent stock a single cent is a 50% gain, so the top of any percentage-ranked list is dominated by the smallest and thinnest listings, often on trivial dollar volume. Check the absolute turnover before reading anything into it.",
        },
        {
          q: "How often does the data update?",
          a: "The dashboard refreshes every five minutes. Metals prices are scraped on a schedule through the day; company prices and volumes are end-of-day rather than intraday, so the movers list reflects the last completed session.",
        },
      ]}
    />
  );
}
