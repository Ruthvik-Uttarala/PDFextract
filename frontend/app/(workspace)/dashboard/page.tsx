"use client";

import Link from "next/link";
import { useCallback, useState } from "react";

import { JobTable } from "@/components/job-table";
import { StatusBadge } from "@/components/status-badge";
import { useAuth } from "@/components/providers/auth-provider";
import { usePollingResource } from "@/hooks/use-polling-resource";
import { listJobs, downloadJobOutput } from "@/lib/api/client";
import { triggerBrowserDownload } from "@/lib/download";
import type { JobSummary } from "@/lib/types";

export default function DashboardPage() {
  const auth = useAuth();
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const loadJobs = useCallback(async (): Promise<JobSummary[]> => {
    const token = await auth.getAccessToken();
    if (!token) {
      return [];
    }
    return listJobs(token);
  }, [auth]);

  const { data, loading, error } = usePollingResource<JobSummary[]>({
    enabled: auth.phase === "authenticated",
    load: loadJobs,
    pollWhen: (jobs) => (jobs || []).some((job) => job.status === "queued" || job.status === "processing"),
    dependencies: [auth.backendUser?.id]
  });

  const jobs = data || [];
  const recentJobs = jobs.slice(0, 5);
  const processingJobs = jobs.filter((job) => job.status === "queued" || job.status === "processing");
  const readyJobs = jobs.filter((job) => job.status === "completed" && job.output_ready).slice(0, 3);

  async function handleDownload(job: JobSummary): Promise<void> {
    const token = await auth.getAccessToken();
    if (!token) {
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

  return (
    <section className="page-grid">
      <header className="page-header">
        <div>
          <p className="page-header__eyebrow">Dashboard</p>
          <h2 className="page-header__title">Upload, track, and download with confidence</h2>
          <p className="page-header__body">
            This workspace shows what you can do now, what is still processing, and which outputs are ready.
          </p>
        </div>
        <Link href="/upload" className="button button--primary">
          Upload PDF
        </Link>
      </header>

      <div className="stat-grid">
        <article className="card stat-card">
          <p className="stat-card__label">Latest uploads</p>
          <strong className="stat-card__value">{jobs.length}</strong>
          <p className="stat-card__hint">Newest-first history across your jobs.</p>
        </article>
        <article className="card stat-card">
          <p className="stat-card__label">Processing now</p>
          <strong className="stat-card__value">{processingJobs.length}</strong>
          <p className="stat-card__hint">Queued and active jobs still moving through the pipeline.</p>
        </article>
        <article className="card stat-card">
          <p className="stat-card__label">Ready downloads</p>
          <strong className="stat-card__value">{readyJobs.length}</strong>
          <p className="stat-card__hint">Completed outputs that already exist in storage.</p>
        </article>
      </div>

      {error ? <div className="notice notice--error">{error}</div> : null}
      {downloadError ? <div className="notice notice--error">{downloadError}</div> : null}

      <div className="content-grid">
        <section className="card">
          <div className="section-header">
            <div>
              <p className="section-header__eyebrow">Next action</p>
              <h3 className="section-header__title">Upload a new PDF when you are ready</h3>
            </div>
            <Link href="/upload" className="button button--secondary">
              Go to upload
            </Link>
          </div>
          <p className="body-copy">
            PDFextract accepts one PDF per job. After upload, you are routed straight to the job detail screen.
          </p>
        </section>

        <section className="card">
          <div className="section-header">
            <div>
              <p className="section-header__eyebrow">Ready downloads</p>
              <h3 className="section-header__title">Completed outputs</h3>
            </div>
          </div>

          {readyJobs.length === 0 ? (
            <p className="empty-copy">No completed Excel outputs are ready yet.</p>
          ) : (
            <div className="stack-list">
              {readyJobs.map((job) => (
                <article key={job.job_id} className="list-card">
                  <div>
                    <p className="list-card__title">{job.source_filename}</p>
                    <p className="list-card__meta">{job.document_type || "Document"} ready for download</p>
                  </div>
                  <div className="list-card__actions">
                    <StatusBadge status={job.status} />
                    <button className="button button--primary button--small" onClick={() => void handleDownload(job)}>
                      Download Excel
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>

      <section className="card">
        <div className="section-header">
          <div>
            <p className="section-header__eyebrow">Recent jobs</p>
            <h3 className="section-header__title">Newest uploads first</h3>
          </div>
          <Link href="/jobs" className="button button--ghost">
            Open all jobs
          </Link>
        </div>
        {loading && jobs.length === 0 ? <p className="empty-copy">Loading recent jobs...</p> : <JobTable jobs={recentJobs} />}
      </section>
    </section>
  );
}
