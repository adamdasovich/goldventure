"use client";

import { useState } from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import LogoMono from "@/components/LogoMono";
import ChatInterface from "@/components/ChatInterface";

const EXAMPLE_QUERIES = [
  "Summarize the most recent NI 43-101 report for Aston Bay",
  "What are the resource estimates in the latest technical report?",
  "Compare the NPV from the PEA against the current market cap",
  "Extract the sensitivity table from the feasibility study",
  "What are the key risks identified in the technical report?",
  "What gold price assumption was used in the economic study?",
];

export default function NI43101AnalyzerPage() {
  return (
    <div className="min-h-screen bg-slate-900">
      {/* Nav */}
      <nav className="glass-nav sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center">
              <LogoMono className="h-10" />
            </Link>
            <div className="flex items-center gap-2">
              <Link href="/investor-tools">
                <Button variant="ghost" size="sm">
                  All Tools
                </Button>
              </Link>
              <Link href="/companies">
                <Button variant="ghost" size="sm">
                  Companies
                </Button>
              </Link>
              <Link href="/">
                <Button variant="ghost" size="sm">
                  Home
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <section className="py-8 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-[#0a0e1a] to-slate-900">
        <div className="max-w-4xl mx-auto text-center">
          <Badge variant="gold" className="mb-3">
            AI-Powered
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-bold text-gradient-gold mb-3">
            NI 43-101 Report Analyzer
          </h1>
          <p className="text-slate-300 max-w-xl mx-auto mb-4">
            Ask Claude to analyze any technical report in the database. Get
            structured summaries, extract resource data, and compare economics —
            all powered by RAG search across processed documents.
          </p>
          <p className="text-sm text-slate-400 max-w-xl mx-auto">
            New to NI 43-101? Read our{" "}
            <Link
              href="/guides/how-to-read-ni-43-101-report"
              className="text-gold-400 hover:underline"
            >
              plain-English guide to reading an NI 43-101 report
            </Link>{" "}
            — covers the five sections that matter, resource categories, and 10
            red flags to spot a weak report.
          </p>
        </div>
      </section>

      {/* Example Queries */}
      <section className="px-4 sm:px-6 lg:px-8 pb-4">
        <div className="max-w-4xl mx-auto">
          <p className="text-xs text-slate-500 mb-2 text-center">Try asking:</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {EXAMPLE_QUERIES.map((q, i) => (
              <span
                key={i}
                className="text-xs px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700/50 text-slate-400"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Chat Interface */}
      <section className="py-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <ChatInterface />
        </div>
      </section>

      {/* Info */}
      <section className="py-6 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="glass-card rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gold-400 mb-3">
              How it works
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm text-slate-400">
              <div>
                <span className="text-gold-400 font-bold mr-2">1.</span>
                Documents are processed with Docling (GPU-accelerated PDF
                extraction) and stored as vector embeddings.
              </div>
              <div>
                <span className="text-gold-400 font-bold mr-2">2.</span>
                Your question triggers hybrid search: vector similarity + BM25
                keyword matching + cross-encoder re-ranking.
              </div>
              <div>
                <span className="text-gold-400 font-bold mr-2">3.</span>
                Claude receives the most relevant document chunks as context and
                provides sourced, structured answers.
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
