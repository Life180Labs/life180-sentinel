"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { api, EvaluationRun, Report } from "@/lib/api";

// ─── Grade / readiness metadata ──────────────────────────────────────────────

const GRADE_META: Record<string, { color: string; label: string; sublabel: string }> = {
  "A+": { color: "text-emerald-400", label: "Exceptional",    sublabel: "Industry-leading quality" },
  "A":  { color: "text-emerald-400", label: "Excellent",      sublabel: "Production ready" },
  "A-": { color: "text-emerald-400", label: "Very Good",      sublabel: "Production ready, minor gaps" },
  "B+": { color: "text-green-400",   label: "Good",           sublabel: "Production ready with improvements" },
  "B":  { color: "text-green-400",   label: "Above Average",  sublabel: "Stable, some work needed" },
  "B-": { color: "text-green-400",   label: "Satisfactory",   sublabel: "Works, but gaps to address" },
  "C+": { color: "text-yellow-400",  label: "Adequate",       sublabel: "Needs improvement before launch" },
  "C":  { color: "text-yellow-400",  label: "Below Average",  sublabel: "Significant issues present" },
  "C-": { color: "text-yellow-400",  label: "Needs Work",     sublabel: "Not recommended for production" },
  "D":  { color: "text-orange-400",  label: "Poor",           sublabel: "Major rework required" },
  "F":  { color: "text-red-400",     label: "Critical",       sublabel: "Fundamental issues, not shippable" },
};

type ReadinessTier = { label: string; bg: string; text: string; border: string; dot: string };
const READINESS: { min: number; tier: ReadinessTier }[] = [
  { min: 80, tier: { label: "Production Ready",        bg: "bg-emerald-950/60", text: "text-emerald-300", border: "border-emerald-700", dot: "bg-emerald-400" } },
  { min: 65, tier: { label: "Ready With Conditions",   bg: "bg-green-950/60",   text: "text-green-300",   border: "border-green-700",   dot: "bg-green-400"   } },
  { min: 50, tier: { label: "Needs Improvement",       bg: "bg-amber-950/60",   text: "text-amber-300",   border: "border-amber-700",   dot: "bg-amber-400"   } },
  { min: 0,  tier: { label: "Not Production Ready",    bg: "bg-red-950/60",     text: "text-red-300",     border: "border-red-700",     dot: "bg-red-500"     } },
];

function getReadiness(score: number): ReadinessTier {
  return (READINESS.find((r) => score >= r.min) ?? READINESS[READINESS.length - 1]).tier;
}

// ─── Executive summary section parsing ───────────────────────────────────────

const SECTION_ICONS: Record<string, string> = {
  "What Works Well":                "✓",
  "What Needs Attention":           "!",
  "Security Concerns":              "S",
  "Performance & Reliability Risks":"P",
  "Bottom Line":                    "→",
};

const SECTION_COLORS: Record<string, string> = {
  "What Works Well":                "border-emerald-700 bg-emerald-950/40",
  "What Needs Attention":           "border-amber-700 bg-amber-950/40",
  "Security Concerns":              "border-red-700 bg-red-950/40",
  "Performance & Reliability Risks":"border-orange-700 bg-orange-950/40",
  "Bottom Line":                    "border-violet-700 bg-violet-950/40",
};

const SECTION_HEADING_COLORS: Record<string, string> = {
  "What Works Well":                "text-emerald-400",
  "What Needs Attention":           "text-amber-400",
  "Security Concerns":              "text-red-400",
  "Performance & Reliability Risks":"text-orange-400",
  "Bottom Line":                    "text-violet-400",
};

const KNOWN_SUMMARY_HEADINGS = Object.keys(SECTION_ICONS);

function parseSummarySections(text: string): { heading: string; body: string }[] {
  const escaped = KNOWN_SUMMARY_HEADINGS.map((h) => h.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const sectionPattern = new RegExp(`\\*\\*(${escaped.join("|")})\\*\\*`, "g");
  const parts: { heading: string; index: number; start: number }[] = [];
  let match: RegExpExecArray | null;
  while ((match = sectionPattern.exec(text)) !== null) {
    parts.push({ heading: match[1], index: match.index, start: match.index + match[0].length });
  }
  const sections: { heading: string; body: string }[] = [];
  for (let i = 0; i < parts.length; i++) {
    const end = i + 1 < parts.length ? parts[i + 1].index : text.length;
    const body = text.slice(parts[i].start, end).trim();
    if (body) sections.push({ heading: parts[i].heading, body });
  }
  return sections;
}

// ─── ScoreRing ────────────────────────────────────────────────────────────────

function ScoreRing({ score, grade }: { score: number; grade: string }) {
  const meta = GRADE_META[grade] ?? { color: "text-zinc-400", label: "Unknown", sublabel: "" };
  const barColor = score >= 80 ? "bg-emerald-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="flex flex-col items-center gap-1 min-w-[120px]">
      <span className={`text-5xl font-bold tabular-nums ${meta.color}`}>{score}</span>
      <div className="flex items-center gap-1.5">
        <span className={`text-2xl font-semibold ${meta.color}`}>{grade}</span>
        <span className={`text-xs font-medium ${meta.color} opacity-80`}>— {meta.label}</span>
      </div>
      <div className="w-24 h-1.5 rounded-full bg-zinc-700 mt-1">
        <div className={`h-full rounded-full ${barColor}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-[10px] text-zinc-500 text-center mt-0.5">{meta.sublabel}</span>
    </div>
  );
}

// ─── Version history timeline ─────────────────────────────────────────────────

function fmtDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}
function fmtTime(iso: string) {
  return new Date(iso).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}
function fmtDatetime(iso: string) {
  return `${fmtDate(iso)}  ${fmtTime(iso)}`;
}

function HistoryTimeline({
  history,
  viewingRun,
  currentRun,
  onSelectRun,
  loadingRun,
}: {
  history: EvaluationRun[];
  viewingRun: number;
  currentRun: number;
  onSelectRun: (run: number) => void;
  loadingRun: number | null;
}) {
  if (history.length <= 1) return null;
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900/60 p-5">
      <div className="flex items-center justify-between mb-4">
        <p className="text-xs font-medium text-zinc-400 uppercase tracking-wider">
          Evaluation History — {history.length} runs
        </p>
        {viewingRun !== currentRun && (
          <button
            onClick={() => onSelectRun(currentRun)}
            className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
          >
            ← Back to latest (Run #{currentRun})
          </button>
        )}
      </div>
      <div className="flex flex-wrap gap-2">
        {history.map((run) => {
          const meta = GRADE_META[run.grade] ?? { color: "text-zinc-400", label: "" };
          const isViewing = run.run === viewingRun;
          const isCurrent = run.run === currentRun;
          const isLoading = loadingRun === run.run;
          const delta = run.run > 1
            ? (() => {
                const prev = history.find((h) => h.run === run.run - 1);
                if (!prev) return null;
                const d = run.overall_score - prev.overall_score;
                return d === 0 ? null : d;
              })()
            : null;
          return (
            <button
              key={run.run}
              onClick={() => !isViewing && onSelectRun(run.run)}
              disabled={isViewing || isLoading !== false}
              className={`flex flex-col items-center gap-0.5 px-3 py-2 rounded-lg border text-center min-w-[90px] transition-all ${
                isViewing
                  ? "border-violet-600 bg-violet-900/30 cursor-default"
                  : "border-zinc-700 bg-zinc-800/50 hover:border-zinc-500 hover:bg-zinc-800 cursor-pointer"
              }`}
            >
              <span className="text-[10px] text-zinc-500 font-medium">
                Run #{run.run}{isCurrent ? " ✦" : ""}
              </span>
              {isLoading ? (
                <span className="text-zinc-500 text-xs animate-pulse">…</span>
              ) : (
                <>
                  <span className={`text-lg font-bold tabular-nums ${meta.color}`}>{run.overall_score}</span>
                  <span className={`text-xs font-semibold ${meta.color}`}>{run.grade}</span>
                </>
              )}
              {delta != null && (
                <span className={`text-[9px] font-medium ${delta > 0 ? "text-emerald-400" : "text-red-400"}`}>
                  {delta > 0 ? `+${delta}` : `${delta}`}
                </span>
              )}
              <span className="text-[9px] text-zinc-600 leading-tight">
                {fmtDate(run.evaluated_at)}
              </span>
              <span className="text-[9px] text-zinc-700">
                {fmtTime(run.evaluated_at)}
              </span>
              {isViewing && (
                <span className="text-[9px] text-violet-400 font-medium mt-0.5">viewing</span>
              )}
            </button>
          );
        })}
      </div>
      <p className="text-[10px] text-zinc-600 mt-3">
        Click any run to view its full report and download options. ✦ = latest run.
      </p>
    </div>
  );
}

// ─── CategoryCard ─────────────────────────────────────────────────────────────

function CategoryCard({
  category,
  score,
  reasoning,
  confidence,
  findings,
  recommendations,
  recommendation_scores,
  summary,
  created_at,
}: {
  category: string;
  score: number;
  reasoning: string | null;
  confidence: number | null;
  findings: string[];
  recommendations: string[];
  recommendation_scores: number[] | null;
  summary: string | null;
  created_at: string;
}) {
  const [open, setOpen] = useState(false);
  const barColor = score >= 80 ? "bg-emerald-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500";
  const confColor =
    (confidence ?? 0) >= 75 ? "text-emerald-400" :
    (confidence ?? 0) >= 50 ? "text-yellow-400" : "text-orange-400";

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
          {confidence != null && (
            <span className={`text-[10px] font-medium ${confColor}`}>
              {confidence}% conf
            </span>
          )}
          <div className="w-20 h-1.5 rounded-full bg-zinc-700">
            <div className={`h-full rounded-full ${barColor}`} style={{ width: `${score}%` }} />
          </div>
          <span className="text-sm font-semibold tabular-nums w-8 text-right">{score}</span>
          <span className="text-zinc-500 text-xs">{open ? "▲" : "▼"}</span>
        </div>
      </button>

      {open && (
        <div className="px-5 pb-5 border-t border-zinc-800 pt-4 space-y-4">
          {/* Evaluated at timestamp */}
          <p className="text-[10px] text-zinc-600 -mt-1">
            Evaluated: {fmtDatetime(created_at)}
          </p>

          {summary && <p className="text-sm text-zinc-300">{summary}</p>}

          {/* Score reasoning + confidence */}
          {(reasoning || confidence != null) && (
            <div className="rounded-lg bg-zinc-800/60 border border-zinc-700 p-3 space-y-1.5">
              {confidence != null && (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-zinc-500">AI confidence:</span>
                  <div className="flex-1 h-1 rounded-full bg-zinc-700 max-w-[80px]">
                    <div
                      className={`h-full rounded-full ${confColor.replace("text-", "bg-")}`}
                      style={{ width: `${confidence}%` }}
                    />
                  </div>
                  <span className={`text-xs font-medium ${confColor}`}>{confidence}%</span>
                </div>
              )}
              {reasoning && (
                <p className="text-xs text-zinc-400 leading-relaxed italic">{reasoning}</p>
              )}
            </div>
          )}

          {/* Findings — renamed to "What Works Well / Observations" */}
          {findings.length > 0 && (
            <div>
              <p className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">
                What Works Well &amp; Observations
              </p>
              <ol className="space-y-1.5 list-none">
                {findings.map((f, i) => (
                  <li key={i} className="text-sm text-zinc-300 flex gap-2">
                    <span className="text-zinc-500 shrink-0 tabular-nums text-xs pt-0.5 w-5 text-right">
                      {i + 1}.
                    </span>
                    <span>{f.replace(/^\d+\.\s*/, "")}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Recommendations with score impact */}
          {recommendations.length > 0 && (
            <div>
              <p className="text-xs font-medium text-zinc-400 uppercase tracking-wider mb-2">
                Recommendations
              </p>
              <ol className="space-y-2 list-none">
                {recommendations.map((r, i) => {
                  const pts = recommendation_scores?.[i];
                  return (
                    <li key={i} className="flex gap-2">
                      <span className="text-zinc-500 shrink-0 tabular-nums text-xs pt-0.5 w-5 text-right">
                        {i + 1}.
                      </span>
                      <span className="flex-1 text-sm text-zinc-300">
                        {r.replace(/^\d+\.\s*/, "")}
                      </span>
                      {pts != null && (
                        <span className="shrink-0 self-start mt-0.5 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-violet-900/50 text-violet-300 border border-violet-700">
                          +{pts} pts
                        </span>
                      )}
                    </li>
                  );
                })}
              </ol>
              {recommendation_scores && recommendation_scores.length > 0 && (
                <p className="text-[10px] text-zinc-600 mt-2">
                  Total potential gain: +{recommendation_scores.reduce((a, b) => a + b, 0)} pts
                  (estimated path toward 100)
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Download helpers ─────────────────────────────────────────────────────────

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

async function downloadPDF(report: Report) {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });

  const pageW = doc.internal.pageSize.getWidth();
  const pageH = doc.internal.pageSize.getHeight();
  const margin = 18;
  const contentW = pageW - margin * 2;
  const lineH = 5;
  let y = margin;

  // TOC tracking
  const tocEntries: Array<{ title: string; page: number; indent: boolean }> = [];

  const addPage = () => { doc.addPage(); y = margin; };
  const checkY = (needed: number) => { if (y + needed > pageH - margin) addPage(); };

  const currentPage = () => (doc.internal as unknown as { getCurrentPageInfo(): { pageNumber: number } }).getCurrentPageInfo().pageNumber;

  const addTocEntry = (title: string, indent = false) => {
    tocEntries.push({ title, page: currentPage(), indent });
    // PDF bookmark/outline
    (doc as unknown as { outline: { add(parent: null, title: string, opts: { pageNumber: number }): void } })
      .outline.add(null, title, { pageNumber: currentPage() });
  };

  const printWrapped = (
    text: string, x: number, maxW: number, size: number,
    style: string, color: [number, number, number] = [30, 30, 30],
  ) => {
    doc.setFontSize(size);
    doc.setFont("helvetica", style);
    doc.setTextColor(...color);
    const safe = text.replace(/[^\x00-\xFF]/g, "-");
    const lines = doc.splitTextToSize(safe, maxW) as string[];
    checkY(lines.length * lineH + 2);
    doc.text(lines, x, y);
    y += lines.length * lineH;
    return lines.length;
  };

  const readiness = getReadiness(report.overall_score);
  const gradeMeta = GRADE_META[report.grade] ?? { label: "", sublabel: "" };

  // ── Header ──────────────────────────────────────────────────────────────────
  doc.setFillColor(20, 20, 30);
  doc.rect(0, 0, pageW, 42, "F");

  doc.setFontSize(16);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(255, 255, 255);
  doc.text(`${report.owner} / ${report.name}`, margin, 13);

  doc.setFontSize(8);
  doc.setFont("helvetica", "normal");
  doc.setTextColor(160, 160, 180);
  doc.text(report.url, margin, 20);
  const evalTs = report.evaluations.length > 0
    ? new Date(Math.max(...report.evaluations.map((e) => new Date(e.created_at).getTime()))).toLocaleString()
    : new Date(report.generated_at).toLocaleString();
  doc.text(`Run #${report.eval_run}  |  Evaluated: ${evalTs}`, margin, 26);

  // Production readiness badge
  doc.setFontSize(8);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(160, 210, 160);
  doc.text(readiness.label, margin, 33);

  // Score + grade (top right)
  const scoreColor: [number, number, number] =
    report.overall_score >= 80 ? [52, 211, 153] : report.overall_score >= 60 ? [234, 179, 8] : [239, 68, 68];
  doc.setFontSize(26);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(...scoreColor);
  doc.text(`${report.overall_score}`, pageW - margin - 20, 18, { align: "right" });
  doc.setFontSize(11);
  doc.text(report.grade, pageW - margin - 20, 27, { align: "right" });
  doc.setFontSize(7);
  doc.setTextColor(140, 140, 160);
  doc.text(gradeMeta.label, pageW - margin - 20, 33, { align: "right" });

  // Page 1 is reserved for the header + Table of Contents (filled in below, once
  // real page numbers are known); all report content starts on page 2.
  addPage();

  // ── Executive Summary ────────────────────────────────────────────────────────
  if (report.overall_summary) {
    addTocEntry("Executive Summary");
    checkY(20);
    doc.setFontSize(12);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(30, 30, 30);
    doc.text("Executive Summary", margin, y);
    y += 7;

    const sections = parseSummarySections(report.overall_summary);
    if (sections.length > 0) {
      for (const sec of sections) {
        checkY(18);
        doc.setFontSize(9);
        doc.setFont("helvetica", "bold");
        doc.setTextColor(60, 60, 80);
        doc.text(sec.heading, margin, y);
        y += 5;
        // Render body preserving line breaks (numbered lists)
        const bodyLines = sec.body.split("\n").filter(Boolean);
        for (const line of bodyLines) {
          const indent = /^\s*[a-z]\./.test(line) ? margin + 6 : margin + 2;
          printWrapped(line.trim(), indent, contentW - (indent - margin), 9, "normal", [50, 50, 50]);
          y += 1;
        }
        y += 3;
      }
    } else {
      printWrapped(report.overall_summary, margin, contentW, 10, "normal", [40, 40, 40]);
    }
    y += 4;

    doc.setDrawColor(200, 200, 200);
    doc.line(margin, y, pageW - margin, y);
    y += 8;
  }

  // ── Category Scores table ────────────────────────────────────────────────────
  addTocEntry("Category Scores");
  checkY(12);
  doc.setFontSize(12);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(30, 30, 30);
  doc.text("Category Scores", margin, y);
  y += 6;

  const sorted = [...report.evaluations].sort((a, b) => b.score - a.score);
  const scoreColX = pageW - margin - 20;
  const confColX = scoreColX - 18;
  const barStartX = margin + 32;
  const barW = confColX - barStartX - 4;

  for (const ev of sorted) {
    checkY(9);
    const label = ev.category.charAt(0).toUpperCase() + ev.category.slice(1);
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(40, 40, 40);
    doc.text(label, margin, y);

    doc.setFillColor(225, 225, 225);
    doc.roundedRect(barStartX, y - 3.2, barW, 3.5, 1, 1, "F");
    const fc: [number, number, number] = ev.score >= 80 ? [52, 211, 153] : ev.score >= 60 ? [234, 179, 8] : [239, 68, 68];
    doc.setFillColor(...fc);
    doc.roundedRect(barStartX, y - 3.2, Math.max(1, (barW * ev.score) / 100), 3.5, 1, 1, "F");

    doc.setFont("helvetica", "bold");
    doc.setTextColor(40, 40, 40);
    doc.text(`${ev.score}/100`, scoreColX, y, { align: "right" });
    if (ev.confidence != null) {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.setTextColor(120, 120, 140);
      doc.text(`${ev.confidence}%`, confColX, y, { align: "right" });
    }
    y += 7;
  }

  y += 4;
  doc.setDrawColor(200, 200, 200);
  doc.line(margin, y, pageW - margin, y);
  y += 8;

  // ── Detailed Evaluations ─────────────────────────────────────────────────────
  for (const ev of sorted) {
    checkY(22);
    const label = ev.category.charAt(0).toUpperCase() + ev.category.slice(1);
    const fc: [number, number, number] = ev.score >= 80 ? [22, 163, 74] : ev.score >= 60 ? [161, 98, 7] : [185, 28, 28];

    addTocEntry(label, true);

    doc.setFillColor(...fc);
    doc.roundedRect(margin, y - 4.5, contentW, 7, 1.5, 1.5, "F");
    doc.setFontSize(10);
    doc.setFont("helvetica", "bold");
    doc.setTextColor(255, 255, 255);
    doc.text(label, margin + 3, y);
    doc.text(`${ev.score}/100`, pageW - margin - 3, y, { align: "right" });
    y += 8;

    if (ev.reasoning) {
      doc.setFontSize(8);
      doc.setFont("helvetica", "italic");
      doc.setTextColor(80, 80, 100);
      doc.text("Why this score:", margin, y);
      y += 4;
      printWrapped(ev.reasoning, margin + 2, contentW - 2, 8, "italic", [70, 70, 90]);
      y += 3;
    }

    if (ev.summary) {
      printWrapped(ev.summary, margin, contentW, 9, "italic", [70, 70, 70]);
      y += 3;
    }

    if (ev.findings.length > 0) {
      checkY(8);
      doc.setFontSize(9);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(30, 30, 30);
      doc.text("What Works Well & Observations", margin, y);
      y += 4;
      for (let i = 0; i < ev.findings.length; i++) {
        const text = ev.findings[i].replace(/^\d+\.\s*/, "");
        printWrapped(`${i + 1}. ${text}`, margin + 3, contentW - 3, 9, "normal", [40, 40, 40]);
        y += 1.5;
      }
      y += 2;
    }

    if (ev.recommendations.length > 0) {
      checkY(8);
      doc.setFontSize(9);
      doc.setFont("helvetica", "bold");
      doc.setTextColor(30, 30, 30);
      doc.text("Recommendations", margin, y);
      y += 4;
      for (let i = 0; i < ev.recommendations.length; i++) {
        const text = ev.recommendations[i].replace(/^\d+\.\s*/, "");
        const pts = ev.recommendation_scores?.[i];
        const suffix = pts != null ? ` [+${pts} pts]` : "";
        printWrapped(`${i + 1}. ${text}${suffix}`, margin + 3, contentW - 3, 9, "normal", [40, 40, 40]);
        y += 1.5;
      }
    }

    y += 10;
  }

  // ── Table of Contents (filled in on page 1, below the header, now that the
  //    real page numbers for every section are known) ──────────────────────────
  doc.setPage(1);
  (doc as unknown as { outline: { add(parent: null, title: string, opts: { pageNumber: number }): void } })
    .outline.add(null, "Table of Contents", { pageNumber: 1 });

  y = 50;
  doc.setFontSize(14);
  doc.setFont("helvetica", "bold");
  doc.setTextColor(30, 30, 30);
  doc.text("Table of Contents", margin, y);
  y += 10;

  doc.setDrawColor(180, 180, 180);
  doc.line(margin, y, pageW - margin, y);
  y += 7;

  for (const entry of tocEntries) {
    checkY(7);
    const xOffset = entry.indent ? margin + 6 : margin;
    const dotW = pageW - margin * 2 - (entry.indent ? 6 : 0) - 20;

    doc.setFontSize(entry.indent ? 8 : 9);
    doc.setFont("helvetica", entry.indent ? "normal" : "bold");
    doc.setTextColor(40, 40, 40);
    doc.text(entry.title, xOffset, y);

    // Dot leader
    const titleW = doc.getTextWidth(entry.title);
    doc.setTextColor(180, 180, 180);
    doc.setFontSize(8);
    const dots = ".".repeat(Math.floor((dotW - titleW) / doc.getTextWidth(".")));
    doc.text(dots, xOffset + titleW + 2, y);

    // Page number — also add a clickable link
    doc.setFont("helvetica", "bold");
    doc.setTextColor(80, 80, 120);
    doc.text(`${entry.page}`, pageW - margin, y, { align: "right" });
    doc.link(margin, y - 5, contentW, 6, { pageNumber: entry.page });

    y += entry.indent ? 6 : 8;
  }

  doc.save(`${report.owner}-${report.name}-evaluation-run${report.eval_run}.pdf`);
}

// ─── Main page ────────────────────────────────────────────────────────────────

const ACTIVE_STATUSES = ["pending", "cloning", "cloned", "scanning", "scanned", "evaluating"];

export default function RepositoryReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [report, setReport] = useState<Report | null>(null);
  const [history, setHistory] = useState<EvaluationRun[]>([]);
  const [latestRun, setLatestRun] = useState<number>(1);
  const [loadingRun, setLoadingRun] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [reEvaluating, setReEvaluating] = useState(false);

  const loadHistory = (repoId: string) =>
    api.repositories.history(repoId).then(setHistory).catch(() => {});

  useEffect(() => {
    api.reports
      .get(id)
      .then((r) => {
        setReport(r);
        setLatestRun(r.eval_run);
        loadHistory(id);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load report"));
  }, [id]);

  useEffect(() => {
    if (!reEvaluating) return;
    const interval = setInterval(async () => {
      try {
        const repo = await api.repositories.get(id);
        if (!ACTIVE_STATUSES.includes(repo.status)) {
          setReEvaluating(false);
          const updated = await api.reports.get(id);
          setReport(updated);
          setLatestRun(updated.eval_run);
          loadHistory(id);
        }
      } catch {
        setReEvaluating(false);
      }
    }, 4000);
    return () => clearInterval(interval);
  }, [id, reEvaluating]);

  const handleSelectRun = async (run: number) => {
    setLoadingRun(run);
    try {
      const r = await api.reports.get(id, run);
      setReport(r);
    } catch {
      // leave current report on error
    } finally {
      setLoadingRun(null);
    }
  };

  const handleReEvaluate = async () => {
    setReEvaluating(true);
    setError(null);
    try {
      await api.repositories.reEvaluate(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Re-evaluation failed");
      setReEvaluating(false);
    }
  };

  if (error) {
    return (
      <div className="flex flex-col min-h-screen items-center justify-center gap-4">
        <p className="text-red-400">{error}</p>
        <Link href="/" className="text-sm text-violet-400 hover:text-violet-300">Back to dashboard</Link>
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
  const filename = `${report.owner}-${report.name}-run${report.eval_run}`;
  const evaluatedAt = sorted.length > 0
    ? new Date(Math.max(...sorted.map((e) => new Date(e.created_at).getTime())))
    : null;
  const readiness = getReadiness(report.overall_score);
  const strengths = sorted.slice(0, 3);
  const improvements = [...sorted].reverse().slice(0, 3);
  const isViewingHistory = report.eval_run !== latestRun;

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <Link href="/" className="text-zinc-400 hover:text-zinc-200 text-sm transition-colors">← Dashboard</Link>
          <span className="text-zinc-700">/</span>
          <span className="text-sm font-medium">{report.owner}/{report.name}</span>
          <span className="ml-2 text-xs text-zinc-600">Run #{report.eval_run}</span>
          {isViewingHistory && (
            <span className="ml-1 text-xs px-1.5 py-0.5 rounded bg-amber-900/50 text-amber-400 border border-amber-700">
              historical
            </span>
          )}
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10 space-y-8">

        {/* Hero: score + meta + actions */}
        <section className="flex flex-col sm:flex-row gap-8 items-start">
          <ScoreRing score={report.overall_score} grade={report.grade} />
          <div className="flex-1 space-y-3">
            <h1 className="text-2xl font-bold">{report.owner}/{report.name}</h1>
            <a href={report.url} target="_blank" rel="noopener noreferrer"
              className="text-sm text-violet-400 hover:text-violet-300 transition-colors block">
              {report.url}
            </a>
            {report.default_branch && (
              <p className="text-xs text-zinc-500">Branch: {report.default_branch}</p>
            )}
            {evaluatedAt && (
              <p className="text-xs text-zinc-500">
                Evaluated: <span className="text-zinc-400">{fmtDatetime(evaluatedAt.toISOString())}</span>
              </p>
            )}

            {/* Production readiness banner */}
            <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm font-semibold ${readiness.bg} ${readiness.text} ${readiness.border}`}>
              <span className={`w-2 h-2 rounded-full ${readiness.dot}`} />
              {readiness.label}
            </div>

            <div className="flex flex-wrap gap-2 pt-1">
              <button
                onClick={() => downloadBlob(report.markdown_report, `${filename}.md`, "text/markdown")}
                disabled={reEvaluating}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-xs font-medium transition-colors disabled:opacity-40"
              >
                ↓ Markdown {isViewingHistory && `(Run #${report.eval_run})`}
              </button>
              <button
                disabled={pdfLoading || reEvaluating}
                onClick={async () => {
                  setPdfLoading(true);
                  try { await downloadPDF(report); } finally { setPdfLoading(false); }
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 text-xs font-medium transition-colors disabled:opacity-40"
              >
                {pdfLoading ? "Generating…" : `↓ PDF${isViewingHistory ? ` (Run #${report.eval_run})` : ""}`}
              </button>
              {!isViewingHistory && (
                <button
                  disabled={reEvaluating}
                  onClick={handleReEvaluate}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-violet-600 bg-violet-700/30 hover:bg-violet-700/50 text-xs font-medium text-violet-300 transition-colors disabled:opacity-50"
                >
                  {reEvaluating ? (
                    <>
                      <span className="animate-spin inline-block w-3 h-3 border border-violet-400 border-t-transparent rounded-full" />
                      Re-evaluating…
                    </>
                  ) : "↻ Re-evaluate"}
                </button>
              )}
            </div>

            {reEvaluating && (
              <p className="text-xs text-zinc-500">
                Fetching latest code and running fresh AI evaluation — this takes a few minutes…
              </p>
            )}
            {isViewingHistory && (
              <p className="text-xs text-amber-500/80">
                Viewing historical run #{report.eval_run} — executive summary not available for past runs.
                <button onClick={() => handleSelectRun(latestRun)} className="ml-1.5 underline hover:text-amber-400">
                  Switch to latest
                </button>
              </p>
            )}
          </div>
        </section>

        {/* Version history */}
        {history.length > 1 && (
          <HistoryTimeline
            history={history}
            viewingRun={report.eval_run}
            currentRun={latestRun}
            onSelectRun={handleSelectRun}
            loadingRun={loadingRun}
          />
        )}

        {/* Executive Summary */}
        <section className="rounded-xl border border-zinc-700 bg-zinc-900/60 p-6 space-y-5">
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Executive Summary</h2>

          {report.overall_summary ? (
            (() => {
              const sections = parseSummarySections(report.overall_summary!);
              return sections.length > 0 ? (
                <div className="space-y-3">
                  {sections.map((sec) => (
                    <div key={sec.heading}
                      className={`rounded-lg border p-4 ${SECTION_COLORS[sec.heading] ?? "border-zinc-700 bg-zinc-800/40"}`}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-bold font-mono w-5 text-center">
                          {SECTION_ICONS[sec.heading] ?? "•"}
                        </span>
                        <h3 className={`text-sm font-semibold ${SECTION_HEADING_COLORS[sec.heading] ?? "text-zinc-300"}`}>
                          {sec.heading}
                        </h3>
                      </div>
                      <p className="text-sm text-zinc-300 leading-relaxed whitespace-pre-line pl-7">
                        {sec.body}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-zinc-200 leading-relaxed whitespace-pre-line">{report.overall_summary}</p>
              );
            })()
          ) : (
            <p className="text-sm text-zinc-500 italic">
              Summary not available. Re-evaluate to generate one.
            </p>
          )}

          <div className="grid sm:grid-cols-2 gap-4 pt-2 border-t border-zinc-800">
            <div className="space-y-2">
              <p className="text-xs font-medium text-emerald-400 uppercase tracking-wider">Top Strengths</p>
              <ul className="space-y-2">
                {strengths.map((ev) => (
                  <li key={ev.category} className="flex items-start gap-2">
                    <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5" />
                    <div>
                      <span className="text-xs font-medium capitalize text-zinc-200">{ev.category}</span>
                      <span className="text-xs text-zinc-500 ml-1.5">({ev.score}/100)</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
            <div className="space-y-2">
              <p className="text-xs font-medium text-amber-400 uppercase tracking-wider">Needs Attention</p>
              <ul className="space-y-2">
                {improvements.map((ev) => (
                  <li key={ev.category} className="flex items-start gap-2">
                    <span className="shrink-0 w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5" />
                    <div>
                      <span className="text-xs font-medium capitalize text-zinc-200">{ev.category}</span>
                      <span className="text-xs text-zinc-500 ml-1.5">({ev.score}/100)</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </section>

        {/* Category breakdown */}
        <section>
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-4">Category Evaluations</h2>
          <div className="space-y-3">
            {sorted.map((ev) => (
              <CategoryCard
                key={ev.category}
                category={ev.category}
                score={ev.score}
                reasoning={ev.reasoning}
                confidence={ev.confidence}
                findings={ev.findings}
                recommendations={ev.recommendations}
                recommendation_scores={ev.recommendation_scores}
                summary={ev.summary}
                created_at={ev.created_at}
              />
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}
