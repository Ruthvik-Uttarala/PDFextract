"use client";

import Link from "next/link";
import Image from "next/image";
import { useCallback, useMemo, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { usePollingResource } from "@/hooks/use-polling-resource";
import {
  downloadJobImage,
  downloadJobJson,
  downloadJobOutput,
  downloadJobTableCsv,
  downloadJobText,
  getJobDetail,
} from "@/lib/api/client";
import { triggerBrowserDownload } from "@/lib/download";
import { getApiBaseUrl } from "@/lib/env";
import { formatFileSize, formatTimestamp } from "@/lib/format";
import type { JobDetail, JobTimelineItem } from "@/lib/types";

type ResultTab = "text" | "tables" | "images" | "json";

export default function JobDetailPage({ params }: { params: { jobId: string } }) {
  const auth = useAuth();
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [infoMessage, setInfoMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<ResultTab>("text");

  const loadJob = useCallback(async (): Promise<JobDetail> => getJobDetail(params.jobId), [params.jobId]);

  const {
    data: job,
    loading,
    error,
    refresh,
  } = usePollingResource<JobDetail>({
    enabled: auth.phase === "authenticated",
    load: loadJob,
    pollWhen: (value) => value?.status === "queued" || value?.status === "processing",
    dependencies: [auth.backendUser?.id, params.jobId],
  });

  const processingPercent = useMemo(
    () => (job ? getProcessingPercent(job.current_stage, job.status) : 0),
    [job],
  );
  const extractionJsonPayload = job?.extraction?.normalized_json || job?.extraction?.extracted_json || {};
  const extractedImages = job?.extraction?.images || [];

  async function handleDownloadExcel(): Promise<void> {
    if (!job) {
      return;
    }

    try {
      const blob = await downloadJobOutput(job.job_id);
      triggerBrowserDownload(blob, job.source_filename.replace(/\.pdf$/i, ".xlsx"));
      setDownloadError(null);
    } catch (reason) {
      setDownloadError(reason instanceof Error ? reason.message : "Download failed.");
    }
  }

  function handleCopyText(): void {
    const text = job?.extraction?.text_preview || "";
    if (!text) {
      setInfoMessage("No extracted text available yet.");
      return;
    }
    void navigator.clipboard.writeText(text).then(
      () => setInfoMessage("Text copied to clipboard."),
      () => setInfoMessage("Clipboard copy is unavailable in this browser."),
    );
  }

  async function handleDownloadText(): Promise<void> {
    if (!job?.extraction?.text_preview) {
      setInfoMessage("No extracted text available yet.");
      return;
    }
    try {
      const blob = await downloadJobText(job.job_id);
      triggerBrowserDownload(blob, job.source_filename.replace(/\.pdf$/i, ".txt"));
      setInfoMessage(null);
    } catch (reason) {
      setInfoMessage(reason instanceof Error ? reason.message : "Text download failed.");
    }
  }

  async function handleDownloadJson(): Promise<void> {
    if (!job) {
      return;
    }
    try {
      const blob = await downloadJobJson(job.job_id);
      triggerBrowserDownload(blob, job.source_filename.replace(/\.pdf$/i, ".json"));
      setInfoMessage(null);
    } catch (reason) {
      setInfoMessage(reason instanceof Error ? reason.message : "JSON download failed.");
    }
  }

  function handleCopyJson(): void {
    const payload = JSON.stringify(extractionJsonPayload, null, 2);
    if (!payload || payload === "{}") {
      setInfoMessage("No extraction payload is available yet.");
      return;
    }
    void navigator.clipboard.writeText(payload).then(
      () => setInfoMessage("JSON copied to clipboard."),
      () => setInfoMessage("Clipboard copy is unavailable in this browser."),
    );
  }

  async function handleDownloadTableCsv(tableIndex: number, name: string): Promise<void> {
    if (!job) {
      return;
    }
    try {
      const blob = await downloadJobTableCsv(job.job_id, tableIndex);
      const safeName = name.toLowerCase().replace(/[^a-z0-9]+/g, "_");
      triggerBrowserDownload(blob, `${safeName || `table_${tableIndex}`}.csv`);
      setInfoMessage(null);
    } catch (reason) {
      setInfoMessage(reason instanceof Error ? reason.message : "Table download failed.");
    }
  }

  async function handleDownloadImage(imageId: string, name: string): Promise<void> {
    if (!job) {
      return;
    }
    try {
      const blob = await downloadJobImage(job.job_id, imageId);
      triggerBrowserDownload(blob, name);
      setInfoMessage(null);
    } catch (reason) {
      setInfoMessage(reason instanceof Error ? reason.message : "Image download failed.");
    }
  }

  if (loading && !job) {
    return <section className="workspace-page"><p className="empty-copy">Loading job detail...</p></section>;
  }

  if (!job) {
    return (
      <section className="workspace-page">
        <div className="notice notice--error">{error || "The job could not be loaded."}</div>
      </section>
    );
  }

  const isProcessing = job.status === "queued" || job.status === "processing";

  return (
    <section className="workspace-page">
      {error ? <div className="notice notice--error">{error}</div> : null}
      {downloadError ? <div className="notice notice--error">{downloadError}</div> : null}
      {infoMessage ? <div className="notice notice--info">{infoMessage}</div> : null}

      {isProcessing ? (
        <ProcessingPanel
          fileName={job.source_filename}
          fileSizeBytes={job.source_file_size_bytes}
          timeline={job.timeline}
          percent={processingPercent}
        />
      ) : job.status === "failed" ? (
        <div className="results-shell">
          <header className="workspace-page__header">
            <h1>Processing could not be completed</h1>
            <p>{job.failure_message || "This document failed during processing. Please upload again."}</p>
          </header>
          <div className="button-row">
            <Link href="/upload" className="button button--primary button--small">
              New File
            </Link>
            <Link href="/jobs" className="button button--secondary button--small">
              Back to Jobs
            </Link>
            <button className="button button--ghost button--small" onClick={() => void refresh()}>
              Refresh
            </button>
          </div>
        </div>
      ) : (
        <div className="results-shell">
          <header className="results-header">
            <div>
              <h1>{job.source_filename}</h1>
              <p>
                {formatFileSize(job.source_file_size_bytes)} • {formatTimestamp(job.submitted_at)}
              </p>
            </div>

            <div className="button-row">
              <button
                className="button button--secondary button--small"
                disabled={!job.download_available}
                onClick={() => void handleDownloadExcel()}
              >
                Download All
              </button>
              <Link href="/upload" className="button button--primary button--small">
                New File
              </Link>
              <button className="button button--ghost button--small" onClick={() => void refresh()}>
                Refresh
              </button>
            </div>
          </header>

          <div className="results-tabs" role="tablist" aria-label="Extraction results tabs">
            {(["text", "tables", "images", "json"] as ResultTab[]).map((tab) => (
              <button
                key={tab}
                type="button"
                className={activeTab === tab ? "results-tab is-active" : "results-tab"}
                onClick={() => setActiveTab(tab)}
                role="tab"
                aria-selected={activeTab === tab}
              >
                {tab.toUpperCase()}
              </button>
            ))}
          </div>

          <section className="results-body">
            {activeTab === "text" ? (
              <div className="results-panel">
                <h2>Extracted Text</h2>
                <pre className="results-text">{job.extraction?.text_preview || "No extracted text available yet."}</pre>
                <div className="button-row">
                  <button className="button button--secondary button--small" onClick={handleCopyText}>
                    Copy Text
                  </button>
                  <button className="button button--secondary button--small" onClick={() => void handleDownloadText()}>
                    Download TXT
                  </button>
                </div>
              </div>
            ) : null}

            {activeTab === "tables" ? (
              <div className="results-panel">
                <h2>Tables Found ({job.extraction?.tables.length || 0})</h2>
                {job.extraction?.tables.length ? (
                  <div className="results-tables">
                    {job.extraction.tables.map((table) => (
                      <article key={table.name} className="results-table-card">
                        <div className="results-table-card__header">
                          <h3>{table.name}</h3>
                          <button
                            className="button button--secondary button--small"
                            onClick={() => void handleDownloadTableCsv(table.table_index, table.name)}
                          >
                            Download CSV
                          </button>
                        </div>
                        <div className="table-scroll">
                          <table className="jobs-table">
                            <thead>
                              <tr>
                                {table.columns.map((column) => (
                                  <th key={column}>{column}</th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {table.rows.map((row, rowIndex) => (
                                <tr key={`${table.name}-${rowIndex}`}>
                                  {row.map((value, colIndex) => (
                                    <td key={`${table.name}-${rowIndex}-${colIndex}`}>{value}</td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="empty-copy">No structured tables were extracted for this file.</p>
                )}
              </div>
            ) : null}

            {activeTab === "images" ? (
              <div className="results-panel">
                <h2>Images Found ({extractedImages.length})</h2>
                {extractedImages.length > 0 ? (
                  <div className="results-images-grid">
                    {extractedImages.map((image) => (
                      <article key={image.id} className="results-image-card">
                        <Image src={`${getApiBaseUrl()}${image.preview_url}`} alt={image.name} width={260} height={170} unoptimized />
                        <p>{image.name}</p>
                        <span>{image.size_label}</span>
                        <button
                          className="button button--secondary button--small"
                          onClick={() => void handleDownloadImage(image.id, image.name)}
                        >
                          Download
                        </button>
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="empty-copy">No images were extracted from this PDF.</p>
                )}
              </div>
            ) : null}

            {activeTab === "json" ? (
              <div className="results-panel">
                <h2>JSON Output</h2>
                <pre className="results-json">{JSON.stringify(extractionJsonPayload, null, 2)}</pre>
                <div className="button-row">
                  <button className="button button--secondary button--small" onClick={() => void handleDownloadJson()}>
                    Download JSON
                  </button>
                  <button className="button button--secondary button--small" onClick={handleCopyJson}>
                    Copy JSON
                  </button>
                </div>
              </div>
            ) : null}
          </section>
        </div>
      )}
    </section>
  );
}

function ProcessingPanel({
  fileName,
  fileSizeBytes,
  timeline,
  percent,
}: {
  fileName: string;
  fileSizeBytes: number | null;
  timeline: JobTimelineItem[];
  percent: number;
}) {
  return (
    <div className="processing-shell">
      <header className="workspace-page__header">
        <h1>Processing your file...</h1>
        <p>Please wait while we extract data from your PDF.</p>
      </header>

      <section className="processing-card">
        <div className="processing-file">
          <p>{fileName}</p>
          <span>{formatFileSize(fileSizeBytes)}</span>
        </div>
        <ol className="processing-steps">
          {timeline.map((item) => (
            <li key={item.stage}>
              <span className="processing-step">
                <span className={`processing-step__indicator is-${item.state}`} aria-hidden="true">
                  {item.state === "completed" ? "✓" : item.state === "current" ? "◌" : "○"}
                </span>
                <span>{item.label}</span>
              </span>
              <strong className={`processing-state is-${item.state}`}>
                {item.state === "current" ? "In progress" : item.state}
              </strong>
            </li>
          ))}
        </ol>

        <div className="processing-progress">
          <div className="processing-progress__track">
            <div className="processing-progress__bar" style={{ width: `${percent}%` }} />
          </div>
          <span>{percent}%</span>
        </div>
      </section>
    </div>
  );
}

function getProcessingPercent(currentStage: string | null, status: JobDetail["status"]): number {
  if (status === "completed") {
    return 100;
  }

  const stageMap: Record<string, number> = {
    upload_received: 10,
    source_stored: 18,
    event_published: 25,
    worker_started: 35,
    pdf_reading: 42,
    gemini_extraction: 55,
    normalization: 65,
    validation: 75,
    excel_generation: 85,
    artifact_storage: 92,
    completion_persisted: 100,
  };
  if (!currentStage) {
    return 10;
  }
  return stageMap[currentStage] ?? 10;
}
