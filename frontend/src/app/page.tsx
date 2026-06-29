"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { api, Repository } from "@/lib/api";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-zinc-600 text-zinc-200",
  cloning: "bg-blue-700 text-blue-100",
  cloned: "bg-blue-600 text-blue-100",
  scanning: "bg-violet-700 text-violet-100",
  scanned: "bg-violet-600 text-violet-100",
  evaluating: "bg-amber-700 text-amber-100",
  done: "bg-emerald-700 text-emerald-100",
  error: "bg-red-700 text-red-100",
};

function StatusBadge({ status }: { status: string }) {
  const cls = STATUS_COLORS[status] ?? "bg-zinc-600 text-zinc-200";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}

const ACTIVE_STATUSES = new Set(["pending", "cloning", "cloned", "scanning", "scanned", "evaluating"]);

export default function Dashboard() {
  const [repos, setRepos] = useState<Repository[]>([]);
  const [url, setUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchRepos = useCallback(async () => {
    try {
      const data = await api.repositories.list();
      setRepos(data);
    } catch {
      // silently fail on background polls
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRepos();
  }, [fetchRepos]);

  useEffect(() => {
    const hasActive = repos.some((r) => ACTIVE_STATUSES.has(r.status));
    if (!hasActive) return;
    const id = setInterval(fetchRepos, 4000);
    return () => clearInterval(id);
  }, [repos, fetchRepos]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    const trimmed = url.trim();
    if (!trimmed) return;
    setSubmitting(true);
    try {
      const repo = await api.repositories.submit(trimmed);
      setRepos((prev) => [repo, ...prev]);
      setUrl("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.repositories.delete(id);
      setRepos((prev) => prev.filter((r) => r.id !== id));
    } catch {
      // ignore
    }
  }

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center gap-3">
          <span className="text-xl font-semibold tracking-tight">Life180 Sentinel</span>
          <span className="text-zinc-500 text-sm">AI repository evaluation</span>
        </div>
      </header>

      <main className="flex-1 max-w-5xl mx-auto w-full px-6 py-10">
        <section className="mb-10">
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-3">
            Evaluate a repository
          </h2>
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="flex-1 rounded-lg bg-zinc-900 border border-zinc-700 px-4 py-2.5 text-sm
                         placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-violet-500"
              disabled={submitting}
            />
            <button
              type="submit"
              disabled={submitting || !url.trim()}
              className="rounded-lg bg-violet-600 hover:bg-violet-500 disabled:opacity-40
                         px-5 py-2.5 text-sm font-medium transition-colors"
            >
              {submitting ? "Submitting…" : "Evaluate"}
            </button>
          </form>
          {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
        </section>

        <section>
          <h2 className="text-sm font-medium text-zinc-400 uppercase tracking-wider mb-3">
            Repositories
          </h2>

          {loading ? (
            <p className="text-zinc-500 text-sm">Loading…</p>
          ) : repos.length === 0 ? (
            <p className="text-zinc-500 text-sm">No repositories yet. Submit a GitHub URL above.</p>
          ) : (
            <div className="divide-y divide-zinc-800 rounded-xl border border-zinc-800 overflow-hidden">
              {repos.map((repo) => (
                <div key={repo.id} className="flex items-center gap-4 px-5 py-4 bg-zinc-900 hover:bg-zinc-800/60 transition-colors">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium truncate">
                        {repo.owner}/{repo.name}
                      </span>
                      <StatusBadge status={repo.status} />
                    </div>
                    <p className="text-xs text-zinc-500 truncate">{repo.url}</p>
                    {repo.error_message && (
                      <p className="text-xs text-red-400 mt-1 truncate">{repo.error_message}</p>
                    )}
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    {repo.status === "done" && (
                      <Link
                        href={`/repositories/${repo.id}`}
                        className="rounded-md bg-violet-700 hover:bg-violet-600 px-3 py-1.5 text-xs font-medium transition-colors"
                      >
                        View Report
                      </Link>
                    )}
                    <button
                      onClick={() => handleDelete(repo.id)}
                      className="rounded-md border border-zinc-700 hover:border-red-600 hover:text-red-400
                                 px-3 py-1.5 text-xs font-medium transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
