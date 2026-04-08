"use client";

import { useCallback, useMemo, useState } from "react";

import { JobTimeline } from "@/components/job-timeline";
import { StatusBadge } from "@/components/status-badge";
import { useAuth } from "@/components/providers/auth-provider";
import { usePollingResource } from "@/hooks/use-polling-resource";
import { downloadJobOutput, getAdminJobDetail, retryAdminJob } from "@/lib/api/client";
import { triggerBrowserDownload } from "@/lib/download";
import { formatTimestamp } from "@/lib/format";
import type { AdminJobDetail } from "@/lib/types";

export default function AdminJobDetailPage({ params }: { params: { jobId: string } }) {
  const auth = useAuth();
  const [notes, setNotes] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [submittingRetry, setSubmittingRetry] = useState(false);

  const loadJob = useCallback(async (): Promise<AdminJobDetail> => {
    const token = await auth.getAccessToken();
    if (!token) {
      throw new Error("Your session expired. Sign in again.");
    }
    return getAdminJobDetail(token, params.jobId);
  }, [auth, params.jobId]);

  const { data: job, loading, error, refresh } = usePollingResource<AdminJobDetail>({
    enabled: auth.phase === "authenticated" && auth.backendUser?.role === "admin",
    load: loadJob,
    pollWhen: (value) => value?.status === "queued" || value?.status === "processing",
    dependencies: [auth.backendUser?.id, auth.backendUser?.role, params.jobId]
  });

  const retryDisabledReason = useMemo(() => {
    if (!job) {
      return null;
    }
    return job.retry.retry_allowed ? null : job.retry.reason || "Retry is not available for this job.";
  }, [job]);

  async function handleRetry(): Promise<void> {
    const token = await auth.getAccessToken();
    if (!token || !job) {
      return;
    }

    try {
      setSubmittingRetry(true);
      const response = await retryAdminJob(token, job.job_id, notes.trim() || undefined);
      setActionError(null);
      setActionMessage(`Retry queued as attempt ${job.retry.attempt_count + 1}. Current status: ${response.status}.`);
      setNotes("");
      await refresh();
    } catch (reason) {
      setActionMessage(null);
      setActionError(reason instanceof Error ? reason.message : "Retry failed.");
    } finally {
      setSubmittingRetry(false);
    }
  }

  async function handleDownload(): Promise<void> {
    const token = await auth.getAccessToken();
    if (!token || !job) {
      return;
    }

    try {
      const blob = await downloadJobOutput(token, job.job_id);
      triggerBrowserDownload(blob, job.source_filename.replace(/\.pdf$/i, ".xlsx"));
      setActionError(null);
    } catch (reason) {
      setActionMessage(null);
      setActionError(reason instanceof Error ? reason.message : "Download failed.");
    }
  }

  if (loading && !job) {
    return (
      <section className="single-column-page">
        <p className="empty-copy">Loading admin job detail...</p>
      </section>
    );
  }

  if (!job) {
    return (
      <section className="single-column-page">
        <div className="notice notice--error">{error || "The admin job detail could not be loaded."}</div>
      </section>
    );
  }

  return (
    <section className="single-column-page">
      <header className="page-header">
        <div>
          <p className="page-header__eyebrow">Admin job detail</p>
          <h2 className="page-header__title">{job.source_filename}</h2>
          <p className="page-header__body">
            Review timeline state, failure codes, storage references, attempt history, and admin retry activity.
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
      {actionError ? <div className="notice notice--error">{actionError}</div> : null}
      {actionMessage ? <div className="notice notice--info">{actionMessage}</div> : null}

      <section className="card detail-grid">
        <div className="meta-card">
          <span className="meta-card__label">Submitted</span>
          <strong>{formatTimestamp(job.submitted_at)}</strong>
        </div>
        <div className="meta-card">
          <span className="meta-card__label">Status</span>
          <strong>{job.status}</strong>
        </div>
        <div className="meta-card">
          <span className="meta-card__label">Failure code</span>
          <strong>{job.failure_code || "None"}</strong>
        </div>
        <div className="meta-card">
          <span className="meta-card__label">Retry eligibility</span>
          <strong>{job.retry.retry_allowed ? "Allowed" : "Blocked"}</strong>
        </div>
      </section>

      <div className="admin-detail-layout">
        <section className="card">
          <div className="section-header">
            <div>
              <p className="section-header__eyebrow">Timeline</p>
              <h3 className="section-header__title">Pipeline progression</h3>
            </div>
          </div>
          <JobTimeline items={job.timeline} />
        </section>

        <section className="card">
          <div className="section-header">
            <div>
              <p className="section-header__eyebrow">Retry control</p>
              <h3 className="section-header__title">Queue a new processing attempt</h3>
            </div>
          </div>
          <div className="stack-list">
            <label className="field">
              <span className="field__label">Operator notes</span>
              <textarea
                className="field__control field__control--textarea"
                rows={4}
                placeholder="Optional retry notes for audit history."
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
              />
            </label>
            {retryDisabledReason ? <p className="helper-copy helper-copy--error">{retryDisabledReason}</p> : null}
            <div className="button-row">
              <button
                className="button button--primary"
                disabled={submittingRetry || !job.retry.retry_allowed}
                onClick={() => void handleRetry()}
              >
                {submittingRetry ? "Queuing retry..." : "Retry job"}
              </button>
              {job.download_available ? (
                <button className="button button--secondary" onClick={() => void handleDownload()}>
                  Download current Excel
                </button>
              ) : null}
            </div>
          </div>
        </section>
      </div>

      <div className="admin-detail-layout">
        <section className="card">
          <div className="section-header">
            <div>
              <p className="section-header__eyebrow">Attempt history</p>
              <h3 className="section-header__title">Processing attempts</h3>
            </div>
          </div>
          {job.attempts.length === 0 ? (
            <p className="empty-copy">No attempts recorded yet.</p>
          ) : (
            <div className="stack-list">
              {job.attempts.map((attempt) => (
                <article key={attempt.processing_attempt_id} className="list-card list-card--stacked">
                  <div className="list-card__header">
                    <p className="list-card__title">Attempt {attempt.attempt_number}</p>
                    <span className="pill">{attempt.status}</span>
                  </div>
                  <dl className="key-value-grid">
                    <div>
                      <dt>Trigger</dt>
                      <dd>{attempt.trigger_type}</dd>
                    </div>
                    <div>
                      <dt>Started</dt>
                      <dd>{formatTimestamp(attempt.started_at)}</dd>
                    </div>
                    <div>
                      <dt>Ended</dt>
                      <dd>{formatTimestamp(attempt.ended_at)}</dd>
                    </div>
                    <div>
                      <dt>Failure code</dt>
                      <dd>{attempt.failure_code || "None"}</dd>
                    </div>
                  </dl>
                  {attempt.failure_message ? (
                    <p className="helper-copy helper-copy--error">{attempt.failure_message}</p>
                  ) : null}
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="card">
          <div className="section-header">
            <div>
              <p className="section-header__eyebrow">Operational detail</p>
              <h3 className="section-header__title">Storage and admin actions</h3>
            </div>
          </div>

          <div className="stack-list">
            <article className="list-card list-card--stacked">
              <p className="list-card__title">Storage references</p>
              <dl className="key-value-grid">
                <div>
                  <dt>Source file id</dt>
                  <dd className="subtle-code">{job.storage.source_file_id || "Not set"}</dd>
                </div>
                <div>
                  <dt>Output file id</dt>
                  <dd className="subtle-code">{job.storage.current_output_file_record_id || "Not set"}</dd>
                </div>
                <div>
                  <dt>Output storage key</dt>
                  <dd className="subtle-code">{job.storage.current_output_storage_key || "Not available"}</dd>
                </div>
              </dl>
            </article>

            <article className="list-card list-card--stacked">
              <p className="list-card__title">Admin actions</p>
              {job.admin_actions.length === 0 ? (
                <p className="empty-copy">No admin actions have been recorded yet.</p>
              ) : (
                <div className="stack-list">
                  {job.admin_actions.map((action) => (
                    <div key={action.admin_action_id} className="activity-row">
                      <div>
                        <p className="activity-row__title">{action.action_type}</p>
                        <p className="activity-row__meta">{formatTimestamp(action.created_at)}</p>
                      </div>
                      <div className="activity-row__notes">{action.notes || "No notes"}</div>
                    </div>
                  ))}
                </div>
              )}
            </article>
          </div>
        </section>
      </div>
    </section>
  );
}
