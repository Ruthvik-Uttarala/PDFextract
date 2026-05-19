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

export async function getCurrentUser(): Promise<UserProfile> {
  return apiFetch<UserProfile>("/api/me", {});
}

export async function uploadPdf(file: File): Promise<JobSummary> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<JobSummary>("/api/uploads", {
    method: "POST",
    body: formData
  });
}

export async function listJobs(): Promise<JobSummary[]> {
  const payload = await apiFetch<{ jobs: JobSummary[] }>("/api/jobs", {});
  return payload.jobs;
}

export async function getJobDetail(jobId: string): Promise<JobDetail> {
  return apiFetch<JobDetail>(`/api/jobs/${jobId}`, {});
}

export async function downloadJobOutput(jobId: string): Promise<Blob> {
  return apiFetchBlob(`/api/jobs/${jobId}/download`);
}

export async function downloadJobJson(jobId: string): Promise<Blob> {
  return apiFetchBlob(`/api/jobs/${jobId}/download/json`);
}

export async function listAdminJobs(): Promise<JobSummary[]> {
  const payload = await apiFetch<{ jobs: JobSummary[] }>("/api/admin/jobs", {});
  return payload.jobs;
}

export async function getAdminJobDetail(jobId: string): Promise<AdminJobDetail> {
  return apiFetch<AdminJobDetail>(`/api/admin/jobs/${jobId}`, {});
}

export async function retryAdminJob(
  jobId: string,
  notes?: string
): Promise<{ job_id: string; processing_attempt_id: string; status: string; current_stage: string | null }> {
  return apiFetch(`/api/admin/jobs/${jobId}/retry`, {
    method: "POST",
    json: notes ? { notes } : {}
  });
}

async function apiFetch<T>(
  path: string,
  options: {
    method?: "GET" | "POST";
    body?: FormData;
    json?: Record<string, unknown>;
  }
): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: options.method || "GET",
    headers: buildHeaders(options.json ? { "Content-Type": "application/json" } : undefined),
    body: options.body || (options.json ? JSON.stringify(options.json) : undefined),
    cache: "no-store"
  });

  if (!response.ok) {
    throw await buildApiError(response);
  }

  return (await response.json()) as T;
}

async function apiFetchBlob(path: string): Promise<Blob> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    method: "GET",
    headers: buildHeaders(),
    cache: "no-store"
  });

  if (!response.ok) {
    throw await buildApiError(response);
  }

  return response.blob();
}

function buildHeaders(extraHeaders?: HeadersInit): HeadersInit {
  return {
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
