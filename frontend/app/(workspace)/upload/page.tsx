"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";
import { uploadPdf } from "@/lib/api/client";

type ExtractionOption = "text" | "tables" | "ocr";

export default function UploadPage() {
  const auth = useAuth();
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [options, setOptions] = useState<Record<ExtractionOption, boolean>>({
    text: true,
    tables: true,
    ocr: false,
  });

  const selectedFileSizeLabel = useMemo(() => {
    if (!selectedFile) {
      return "";
    }
    return `${(selectedFile.size / (1024 * 1024)).toFixed(1)} MB`;
  }, [selectedFile]);

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

    if (file.size <= 0) {
      setMessage("The selected PDF appears to be empty.");
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

  function toggleOption(option: ExtractionOption): void {
    setOptions((current) => ({
      ...current,
      [option]: !current[option],
    }));
  }

  return (
    <section className="workspace-page">
      <header className="workspace-page__header">
        <h1>Extract data from your PDF</h1>
        <p>Upload a PDF file and extract text, tables, and images with ease.</p>
      </header>

      <section className="upload-card">
        <label
          className="upload-zone"
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

          <span className="upload-zone__icon">↑</span>
          <p className="upload-zone__title">Drag &amp; Drop your PDF here</p>
          <p className="upload-zone__subtle">or</p>
          <span className="button button--primary button--small">Upload PDF</span>
        </label>

        {selectedFile ? (
          <div className="upload-selected-file">
            <div>
              <p className="upload-selected-file__name">{selectedFile.name}</p>
              <p className="upload-selected-file__size">{selectedFileSizeLabel}</p>
            </div>
            <button
              type="button"
              className="upload-selected-file__remove"
              onClick={() => setSelectedFile(null)}
              aria-label="Remove selected file"
            >
              ×
            </button>
          </div>
        ) : null}

        <div className="upload-options">
          <label className="upload-option">
            <input
              type="checkbox"
              checked={options.text}
              onChange={() => toggleOption("text")}
            />
            <div>
              <p>Extract Text</p>
              <span>Extract readable text from PDF</span>
            </div>
          </label>
          <label className="upload-option">
            <input
              type="checkbox"
              checked={options.tables}
              onChange={() => toggleOption("tables")}
            />
            <div>
              <p>Extract Tables</p>
              <span>Extract tables in CSV format</span>
            </div>
          </label>
          <label className="upload-option">
            <input
              type="checkbox"
              checked={options.ocr}
              onChange={() => toggleOption("ocr")}
            />
            <div>
              <p>OCR (Scanned PDF)</p>
              <span>Extract text from scanned PDFs</span>
            </div>
          </label>
        </div>

        {message ? <div className="notice notice--error">{message}</div> : null}

        <button className="button button--primary button--wide" disabled={submitting} onClick={() => void handleSubmit()}>
          {submitting ? "Uploading..." : "Extract Now"}
        </button>
      </section>
    </section>
  );
}
