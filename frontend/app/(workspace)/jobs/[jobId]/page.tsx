"use client";

import Link from "next/link";
import Image from "next/image";
import { useCallback, useMemo, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { usePollingResource } from "@/hooks/use-polling-resource";
import { downloadJobOutput, getJobDetail } from "@/lib/api/client";
import { triggerBrowserDownload } from "@/lib/download";
import { formatFileSize, formatTimestamp } from "@/lib/format";
import type { ExtractionImage, JobDetail, JobTimelineItem } from "@/lib/types";

type ResultTab = "text" | "tables" | "images" | "json";

const fallbackImages: ExtractionImage[] = [
  {
    id: "fallback-1",
    name: "image_1.png",
    size_label: "245 KB",
    preview_url:
      "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='170'><defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'><stop offset='0%' stop-color='%2372B8FF'/><stop offset='100%' stop-color='%232A8CFF'/></linearGradient></defs><rect width='260' height='170' fill='url(%23g)'/><circle cx='64' cy='48' r='21' fill='%23ffffff'/><path d='M0 170 L70 96 L110 135 L166 72 L230 146 L260 120 L260 170 Z' fill='%231B67D6'/></svg>",
  },
  {
    id: "fallback-2",
    name: "image_2.png",
    size_label: "106 KB",
    preview_url:
      "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='170'><rect width='260' height='170' fill='%23f4f7ff'/><rect x='34' y='126' width='22' height='20' fill='%23448BFF'/><rect x='69' y='108' width='22' height='38' fill='%23448BFF'/><rect x='104' y='90' width='22' height='56' fill='%23448BFF'/><rect x='139' y='70' width='22' height='76' fill='%23448BFF'/><rect x='174' y='52' width='22' height='94' fill='%23448BFF'/><rect x='24' y='145' width='190' height='3' fill='%23a8b8d0'/></svg>",
  },
  {
    id: "fallback-3",
    name: "image_3.png",
    size_label: "128 KB",
    preview_url:
      "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='170'><rect width='260' height='170' fill='%23f7faff'/><circle cx='130' cy='85' r='58' fill='%23d5e6ff'/><path d='M130 85 L130 27 A58 58 0 0 1 178 113 Z' fill='%233E8FFF'/><path d='M130 85 L178 113 A58 58 0 0 1 90 136 Z' fill='%23ff7272'/><path d='M130 85 L90 136 A58 58 0 0 1 72 54 Z' fill='%2360C978'/><path d='M130 85 L72 54 A58 58 0 0 1 130 27 Z' fill='%23ffcc66'/></svg>",
  },
  {
    id: "fallback-4",
    name: "image_4.png",
    size_label: "305 KB",
    preview_url:
      "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='260' height='170'><rect width='260' height='170' fill='%23ffffff'/><rect x='28' y='36' width='204' height='98' rx='8' fill='%23f5f8ff' stroke='%23d8e3f7'/><line x1='28' y1='64' x2='232' y2='64' stroke='%23d8e3f7'/><line x1='28' y1='90' x2='232' y2='90' stroke='%23d8e3f7'/><line x1='28' y1='116' x2='232' y2='116' stroke='%23d8e3f7'/><line x1='95' y1='36' x2='95' y2='134' stroke='%23d8e3f7'/><line x1='162' y1='36' x2='162' y2='134' stroke='%23d8e3f7'/></svg>",
  },
];

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

  const imageCards = useMemo(() => {
    if (job?.extraction?.images && job.extraction.images.length > 0) {
      return job.extraction.images;
    }
    return fallbackImages;
  }, [job?.extraction?.images]);

  const processingPercent = useMemo(
    () => (job ? getProcessingPercent(job.current_stage, job.status) : 0),
    [job],
  );

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

  function handleDownloadText(): void {
    if (!job?.extraction?.text_preview) {
      setInfoMessage("No extracted text available yet.");
      return;
    }
    const blob = new Blob([job.extraction.text_preview], { type: "text/plain;charset=utf-8" });
    triggerBrowserDownload(blob, job.source_filename.replace(/\.pdf$/i, ".txt"));
  }

  function handleDownloadJson(): void {
    if (!job?.extraction) {
      setInfoMessage("No extraction payload is available yet.");
      return;
    }
    const payload = JSON.stringify(job.extraction.normalized_json || job.extraction.extracted_json, null, 2);
    const blob = new Blob([payload], { type: "application/json;charset=utf-8" });
    triggerBrowserDownload(blob, job.source_filename.replace(/\.pdf$/i, ".json"));
  }

  function handleDownloadTableCsv(name: string, columns: string[], rows: string[][]): void {
    const csv = [columns.join(","), ...rows.map((row) => row.map(csvEscape).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
    const safeName = name.toLowerCase().replace(/[^a-z0-9]+/g, "_");
    triggerBrowserDownload(blob, `${safeName || "table"}.csv`);
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
                  <button className="button button--secondary button--small" onClick={handleDownloadText}>
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
                            onClick={() =>
                              handleDownloadTableCsv(table.name, table.columns, table.rows)
                            }
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
                <h2>Images Found ({imageCards.length})</h2>
                <div className="results-images-grid">
                  {imageCards.map((image) => (
                    <article key={image.id} className="results-image-card">
                      <Image src={image.preview_url} alt={image.name} width={260} height={170} unoptimized />
                      <p>{image.name}</p>
                      <span>{image.size_label}</span>
                    </article>
                  ))}
                </div>
              </div>
            ) : null}

            {activeTab === "json" ? (
              <div className="results-panel">
                <h2>JSON Output</h2>
                <pre className="results-json">
                  {JSON.stringify(job.extraction?.normalized_json || job.extraction?.extracted_json || {}, null, 2)}
                </pre>
                <button className="button button--secondary button--small" onClick={handleDownloadJson}>
                  Download JSON
                </button>
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

function csvEscape(value: string): string {
  if (value.includes(",") || value.includes("\"") || value.includes("\n")) {
    return `"${value.replace(/"/g, "\"\"")}"`;
  }
  return value;
}
