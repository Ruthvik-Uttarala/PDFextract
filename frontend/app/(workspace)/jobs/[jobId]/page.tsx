"use client";

import { useCallback, useState } from "react";

import { JobTimeline } from "@/components/job-timeline";
import { StatusBadge } from "@/components/status-badge";
import { useAuth } from "@/components/providers/auth-provider";
import { usePollingResource } from "@/hooks/use-polling-resource";
import { downloadJobOutput, getJobDetail } from "@/lib/api/client";
import { triggerBrowserDownload } from "@/lib/download";
import { formatTimestamp } from "@/lib/format";
import type { JobDetail } from "@/lib/types";

export default function JobDetailPage({ params }: { params: { jobId: string } }) {
  const auth = useAuth();
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const loadJob = useCallback(async (): Promise<JobDetail> => {
    const token = await auth.getAccessToken();
    if (!token) {
      throw new Error("Your session expired. Sign in again.");
    }
    return getJobDetail(token, params.jobId);
  }, [auth, params.jobId]);

  const { data: job, loading, error, refresh } = usePollingResource<JobDetail>({
    enabled: auth.phase === "authenticated",
    load: loadJob,
    pollWhen: (value) => value?.status === "queued" || value?.status === "processing",
    dependencies: [auth.backendUser?.id, params.jobId]
  });

  async function handleDownload(): Promise<void> {
    const token = await auth.getAccessToken();
    if (!token || !job) {
      return;
    }

    try {
      const blob = await downloadJobOutput(token, job.job_id);
      triggerBrowserDownload(blob, job.source_filename.replace(/\.pdf$/i, ".xlsx"));
      setDownloadError(null);
    } catch (reason) {
      setDownloadError(reason instanceof Error ? reason.message : "Download failed.");
    }
  }

  if (loading && !job) {
    return <section className="single-column-page"><p className="empty-copy">Loading job detail...</p></section>;
  }

  if (!job) {
    return (
      <section className="single-column-page">
        <div className="notice notice--error">{error || "The job could not be loaded."}</div>
      </section>
    );
  }

  return (
    <section className="single-column-page">
      <header className="page-header">
        <div>
          <p className="page-header__eyebrow">Job detail</p>
          <h2 className="page-header__title">{job.source_filename}</h2>
          <p className="page-header__body">
            This page shows the current state, major timeline stages, timestamps, and the real output action.
          </p>
        </div>
        <div className="button-row">
          <StatusBadge status={job.status} />
          <button className="button button--secondary" onClick={() => void refresh()}>
            Refresh
          </button>
        </div>
      </header>

      {error ? <div className="notice notice--error">{error}</div> : null}
      {downloadError ? <div className="notice notice--error">{downloadError}</div> : null}

      <section className="card detail-grid">
        <div className="meta-card">
          <span className="meta-card__label">Submitted</span>
          <strong>{formatTimestamp(job.submitted_at)}</strong>
        </div>
        <div className="meta-card">
          <span className="meta-card__label">Processing started</span>
          <strong>{formatTimestamp(job.processing_started_at)}</strong>
        </div>
        <div className="meta-card">
          <span className="meta-card__label">Completed</span>
          <strong>{formatTimestamp(job.completed_at)}</strong>
        </div>
        <div className="meta-card">
          <span className="meta-card__label">Document type</span>
          <strong>{job.document_type || "Pending detection"}</strong>
        </div>
      </section>

      <section className="card">
        <div className="section-header">
          <div>
            <p className="section-header__eyebrow">Timeline</p>
            <h3 className="section-header__title">Major processing stages</h3>
          </div>
        </div>
        <JobTimeline items={job.timeline} />
      </section>

      <section className="card">
        <div className="section-header">
          <div>
            <p className="section-header__eyebrow">Output</p>
            <h3 className="section-header__title">Excel artifact</h3>
          </div>
        </div>

        {job.download_available ? (
          <div className="stack-list">
            <p className="body-copy">The Excel output is available now.</p>
            <button className="button button--primary" onClick={() => void handleDownload()}>
              Download Excel
            </button>
          </div>
        ) : job.status === "failed" ? (
          <div className="notice notice--error">
            {job.failure_message || "This file could not be processed."}
          </div>
        ) : (
          <div className="notice notice--info">Output is not available yet.</div>
        )}
      </section>
    </section>
  );
}
