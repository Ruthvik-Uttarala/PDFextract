"use client";

import { useCallback } from "react";

import { JobTable } from "@/components/job-table";
import { useAuth } from "@/components/providers/auth-provider";
import { usePollingResource } from "@/hooks/use-polling-resource";
import { listJobs } from "@/lib/api/client";
import type { JobSummary } from "@/lib/types";

export default function JobsPage() {
  const auth = useAuth();

  const loadJobs = useCallback(async (): Promise<JobSummary[]> => {
    const token = await auth.getAccessToken();
    if (!token) {
      return [];
    }
    return listJobs(token);
  }, [auth]);

  const { data, loading, error, refresh } = usePollingResource<JobSummary[]>({
    enabled: auth.phase === "authenticated",
    load: loadJobs,
    pollWhen: (jobs) => (jobs || []).some((job) => job.status === "queued" || job.status === "processing"),
    dependencies: [auth.backendUser?.id]
  });

  const jobs = data || [];

  return (
    <section className="page-grid">
      <header className="page-header">
        <div>
          <p className="page-header__eyebrow">Jobs</p>
          <h2 className="page-header__title">Your full processing history</h2>
          <p className="page-header__body">
            Jobs are listed newest first so current uploads and recent outputs stay easy to scan.
          </p>
        </div>
        <button className="button button--secondary" onClick={() => void refresh()}>
          Refresh
        </button>
      </header>

      <section className="card">
        {error ? <div className="notice notice--error">{error}</div> : null}
        {loading && jobs.length === 0 ? <p className="empty-copy">Loading jobs...</p> : <JobTable jobs={jobs} />}
      </section>
    </section>
  );
}
