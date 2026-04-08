"use client";

import { useCallback } from "react";

import { JobTable } from "@/components/job-table";
import { useAuth } from "@/components/providers/auth-provider";
import { usePollingResource } from "@/hooks/use-polling-resource";
import { listAdminJobs } from "@/lib/api/client";
import type { JobSummary } from "@/lib/types";

export default function AdminJobsPage() {
  const auth = useAuth();

  const loadJobs = useCallback(async (): Promise<JobSummary[]> => {
    const token = await auth.getAccessToken();
    if (!token) {
      return [];
    }
    return listAdminJobs(token);
  }, [auth]);

  const { data, loading, error, refresh } = usePollingResource<JobSummary[]>({
    enabled: auth.phase === "authenticated" && auth.backendUser?.role === "admin",
    load: loadJobs,
    pollWhen: (jobs) => (jobs || []).some((job) => job.status === "queued" || job.status === "processing"),
    dependencies: [auth.backendUser?.id, auth.backendUser?.role]
  });

  const jobs = data || [];
  const failedJobs = jobs.filter((job) => job.status === "failed");

  return (
    <section className="page-grid">
      <header className="page-header">
        <div>
          <p className="page-header__eyebrow">Admin jobs</p>
          <h2 className="page-header__title">Operational view across all document jobs</h2>
          <p className="page-header__body">
            Inspect failures, monitor queue activity, and open retry controls without losing attempt history.
          </p>
        </div>
        <button className="button button--secondary" onClick={() => void refresh()}>
          Refresh
        </button>
      </header>

      <div className="stat-grid">
        <article className="card stat-card">
          <p className="stat-card__label">Total jobs</p>
          <strong className="stat-card__value">{jobs.length}</strong>
          <p className="stat-card__hint">Every job visible to admins, newest first.</p>
        </article>
        <article className="card stat-card">
          <p className="stat-card__label">Failed jobs</p>
          <strong className="stat-card__value">{failedJobs.length}</strong>
          <p className="stat-card__hint">These are candidates for inspection and retry.</p>
        </article>
        <article className="card stat-card">
          <p className="stat-card__label">In flight</p>
          <strong className="stat-card__value">
            {jobs.filter((job) => job.status === "queued" || job.status === "processing").length}
          </strong>
          <p className="stat-card__hint">Queued or processing jobs still moving through the worker pipeline.</p>
        </article>
      </div>

      <section className="card">
        {error ? <div className="notice notice--error">{error}</div> : null}
        {loading && jobs.length === 0 ? (
          <p className="empty-copy">Loading admin jobs...</p>
        ) : (
          <JobTable jobs={jobs} adminView />
        )}
      </section>
    </section>
  );
}
