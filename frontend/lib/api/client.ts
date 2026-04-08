"use client";

import { getApiBaseUrl } from "@/lib/env";
import type { AdminJobDetail, JobDetail, JobSummary, UserProfile } from "@/lib/types";

type ApiErrorPayload = {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
    correlation_id?: string;
  };
};

export class ApiClientError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details?: Record<string, unknown>;

  constructor(message: string, status: number, code = "API_ERROR", details?: Record<string, unknown>) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export async function getCurrentUser(token: string): Promise<UserProfile> {
  return apiFetch<UserProfile>("/api/me", { token });
}

export async function uploadPdf(token: string, file: File): Promise<JobSummary> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<JobSummary>("/api/uploads", {
    method: "POST",
    token,
    body: formData
  });
}

export async function listJobs(token: string): Promise<JobSummary[]> {
  const payload = await apiFetch<{ jobs: JobSummary[] }>("/api/jobs", { token });
  return payload.jobs;
}

export async function getJobDetail(token: string, jobId: string): Promise<JobDetail> {
  return apiFetch<JobDetail>(`/api/jobs/${jobId}`, { token });
}

export async function downloadJobOutput(token: string, jobId: string): Promise<Blob> {
  return apiFetchBlob(`/api/jobs/${jobId}/download`, { token });
}

export async function listAdminJobs(token: string): Promise<JobSummary[]> {
  const payload = await apiFetch<{ jobs: JobSummary[] }>("/api/admin/jobs", { token });
  return payload.jobs;
}

export async function getAdminJobDetail(token: string, jobId: string): Promise<AdminJobDetail> {
  return apiFetch<AdminJobDetail>(`/api/admin/jobs/${jobId}`, { token });
}

export async function retryAdminJob(
  token: string,
  jobId: string,
  notes?: string
): Promise<{ job_id: string; processing_attempt_id: string; status: string; current_stage: string | null }> {
  return apiFetch(`/api/admin/jobs/${jobId}/retry`, {
    method: "POST",
    token,
    json: notes ? { notes } : {}
  });
}

async function apiFetch<T>(
  path: string,
  options: {
    method?: "GET" | "POST";
    token: string;
    body?: FormData;
    json?: Record<string, unknown>;
  }
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: options.method || "GET",
    headers: buildHeaders(options.token, options.json ? { "Content-Type": "application/json" } : undefined),
    body: options.body || (options.json ? JSON.stringify(options.json) : undefined),
    cache: "no-store"
  });

  if (!response.ok) {
    throw await buildApiError(response);
  }

  return (await response.json()) as T;
}

async function apiFetchBlob(
  path: string,
  options: {
    token: string;
  }
): Promise<Blob> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "GET",
    headers: buildHeaders(options.token),
    cache: "no-store"
  });

  if (!response.ok) {
    throw await buildApiError(response);
  }

  return response.blob();
}

function buildHeaders(token: string, extraHeaders?: HeadersInit): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    ...(extraHeaders || {})
  };
}

async function buildApiError(response: Response): Promise<ApiClientError> {
  let payload: ApiErrorPayload | null = null;
  try {
    payload = (await response.json()) as ApiErrorPayload;
  } catch {
    payload = null;
  }

  return new ApiClientError(
    payload?.error?.message || "The backend request failed.",
    response.status,
    payload?.error?.code || "API_ERROR",
    payload?.error?.details
  );
}
