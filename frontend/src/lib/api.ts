const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export interface Repository {
  id: string;
  url: string;
  owner: string;
  name: string;
  status: string;
  default_branch: string | null;
  error_message: string | null;
  created_at: string;
}

export interface CategoryEvaluation {
  id: string;
  repository_id: string;
  category: string;
  score: number;
  findings: string[];
  recommendations: string[];
  summary: string | null;
  created_at: string;
}

export interface EvaluationSummary {
  repository_id: string;
  overall_score: number;
  categories: CategoryEvaluation[];
}

export interface RepositoryScore {
  repository_id: string;
  overall_score: number;
  grade: string;
  category_scores: Record<string, number>;
}

export interface Report {
  repository_id: string;
  owner: string;
  name: string;
  url: string;
  status: string;
  default_branch: string | null;
  overall_score: number;
  grade: string;
  evaluations: CategoryEvaluation[];
  markdown_report: string;
  generated_at: string;
}

export const api = {
  repositories: {
    list: () => request<Repository[]>("/api/v1/repositories/"),
    get: (id: string) => request<Repository>(`/api/v1/repositories/${id}`),
    submit: (url: string) =>
      request<Repository>("/api/v1/repositories/", {
        method: "POST",
        body: JSON.stringify({ url }),
      }),
    delete: (id: string) =>
      request<void>(`/api/v1/repositories/${id}`, { method: "DELETE" }),
  },
  evaluations: {
    get: (id: string) => request<EvaluationSummary>(`/api/v1/repositories/${id}/evaluations`),
  },
  reports: {
    get: (id: string) => request<Report>(`/api/v1/repositories/${id}/report`),
    score: (id: string) => request<RepositoryScore>(`/api/v1/repositories/${id}/score`),
  },
};
