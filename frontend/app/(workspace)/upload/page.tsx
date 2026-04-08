"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { uploadPdf } from "@/lib/api/client";

export default function UploadPage() {
  const auth = useAuth();
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  function handleFileSelection(file: File | null): void {
    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setMessage("Only PDF uploads are supported.");
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
    setMessage(null);
  }

  async function handleSubmit(): Promise<void> {
    if (!selectedFile) {
      setMessage("Choose one PDF to continue.");
      return;
    }

    const token = await auth.getAccessToken();
    if (!token) {
      setMessage("Your session expired. Sign in again.");
      return;
    }

    try {
      setSubmitting(true);
      const job = await uploadPdf(token, selectedFile);
      router.push(`/jobs/${job.job_id}`);
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "Upload failed. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="single-column-page">
      <header className="page-header">
        <div>
          <p className="page-header__eyebrow">Upload</p>
          <h2 className="page-header__title">Create a new document job</h2>
          <p className="page-header__body">
            Upload one PDF. The backend stores it, creates a job, and hands processing to the async pipeline.
          </p>
        </div>
      </header>

      <section className="card">
        <div className="section-header">
          <div>
            <p className="section-header__eyebrow">Source file</p>
            <h3 className="section-header__title">One PDF only</h3>
          </div>
        </div>

        <label
          className="upload-dropzone"
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            handleFileSelection(event.dataTransfer.files.item(0));
          }}
        >
          <input
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => handleFileSelection(event.target.files?.item(0) || null)}
            className="visually-hidden"
          />
          <strong>{selectedFile ? selectedFile.name : "Drop a PDF here or browse from your device"}</strong>
          <span>Accepted format: one `.pdf` file per job.</span>
        </label>

        <div className="meta-grid">
          <div className="meta-card">
            <span className="meta-card__label">Selected file</span>
            <strong>{selectedFile ? selectedFile.name : "None selected"}</strong>
          </div>
          <div className="meta-card">
            <span className="meta-card__label">What happens next</span>
            <strong>Stored, queued, then processed asynchronously</strong>
          </div>
        </div>

        {message ? <div className="notice notice--error">{message}</div> : null}

        <div className="button-row">
          <button className="button button--primary" disabled={submitting} onClick={() => void handleSubmit()}>
            {submitting ? "Uploading..." : "Upload PDF"}
          </button>
        </div>
      </section>
    </section>
  );
}
