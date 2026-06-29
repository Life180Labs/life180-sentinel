"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api, Report } from "@/lib/api";

const GRADE_COLORS: Record<string, string> = {
  "A+": "text-emerald-400",
  A: "text-emerald-400",
  "A-": "text-emerald-400",
  "B+": "text-green-400",
  B: "text-green-400",
  "B-": "text-green-400",
  "C+": "text-yellow-400",
  C: "text-yellow-400",
  "C-": "text-yellow-400",
  D: "text-orange-400",
  F: "text-red-400",
};

function ScoreRing({ score, grade }: { score: number; grade: string }) {
  const gradeColor = GRADE_COLORS[grade] ?? "text-zinc-400";
  const barColor =
    score >= 80 ? "bg-emerald-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="flex flex-col items-center gap-1">
      <span className={`text-5xl font-bold tabular-nums ${gradeColor}`}>{score}</span>
      <span className={`text-2xl font-semibold ${gradeColor}`}>{grade}</span>
      <div className="w-24 h-1.5 rounded-full bg-zinc-700 mt-1">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

function CategoryCard({
  category,
  score,
  findings,
  recommendations,
  summary,
}: {
  category: string;
  score: number;
  findings: string[];
  recommendations: string[];
  summary: string | null;
}) {
  const [open, setOpen] = useState(false);
  const barColor =
    score >= 80 ? "bg-emerald-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-zinc-800/60 transition-colors"
      >
        <div className="flex-1">
          <p className="text-sm font-medium capitalize">{category}</p>
          {summary && !open && (
            <p className="text-xs text-zinc-500 mt-0.5 line-clamp-1">{summary}</p>
          )}
        </div>
        <div className="flex items-center gap-3 shrink-0">
          <div className="w-20 h-1.5 rounded-full bg-zinc-700">
            <div className={`h-full rounded-full ${barColor}`} style={{ width: `${score}%` }} />
          </div>
          <span className="text-sm font-semibold tabular-nums w-8 text-right">{score}</span>
          <span className="text-zinc-500 text-xs">{open ? "▲" : "▼"}</span>
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-zinc-800 pt-4 space-y-4">
          {summary && <p className="text-sm text-zinc-300">{summary}</p>}
          {findings.length > 0 && (
            <div>
              <p className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">Findings</p>
              <ul className="space-y-1.5">
                {findings.map((f, i) => (
                  <li key={i} className="text-sm text-zinc-300 flex gap-2">
                    <span className="text-zinc-600 shrink-0">•</span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {recommendations.length > 0 && (
            <div>
              <p className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">Recommendations</p>
              <ul className="space-y-1.5">
                {recommendations.map((r, i) => (
                  <li key={i} className="text-sm text-zinc-300 flex gap-2">
                    <span className="text-violet-500 shrink-0">→</span>
                    {r}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function RepositoryReportPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.reports
      .get(id)
      .then(setReport)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load report"));
  }, [id]);

  if (error) {
    return (
      <div className="flex flex-col min-h-screen items-center justify-center gap-4">
        <p className="text-red-400">{error}</p>
        <Link href="/" className="text-sm text-violet-400 hover:text-violet-300">
          Back to dashboard
        </Link>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="flex flex-col min-h-screen items-center justify-center">
        <p className="text-zinc-500">Loading report…</p>
      </div>
    );
  }

  const sorted = [...report.evaluations].sort((a, b) => b.score - a.score);

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link href="/" className="text-zinc-400 hover:text-zinc-200 text-sm transition-colors">
            ← Dashboard
          </Link>
          <span className="text-zinc-700">/</span>
          <span className="text-sm font-medium">
            {report.owner}/{report.name}
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10 space-y-10">
        <section className="flex flex-col sm:flex-row gap-8 items-start">
          <ScoreRing score={report.overall_score} grade={report.grade} />
          <div className="flex-1">
            <h1 className="text-2xl font-bold mb-1">
              {report.owner}/{report.name}
            </h1>
            <a
              href={report.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-violet-400 hover:text-violet-300 transition-colors"
            >
              {report.url}
            </a>
            {report.default_branch && (
              <p className="text-xs text-zinc-500 mt-1">Branch: {report.default_branch}</p>
            )}
          </div>
        </section>

        <section>
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-4">
            Category Evaluations
          </h2>
          <div className="space-y-3">
            {sorted.map((ev) => (
              <CategoryCard
                key={ev.category}
                category={ev.category}
                score={ev.score}
                findings={ev.findings}
                recommendations={ev.recommendations}
                summary={ev.summary}
              />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
