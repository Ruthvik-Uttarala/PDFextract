import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import JobDetailPage from "@/app/(workspace)/jobs/[jobId]/page";

const downloadJobOutput = vi.fn();
const downloadJobJson = vi.fn();
const triggerBrowserDownload = vi.fn();
const writeClipboard = vi.fn();

vi.mock("@/components/providers/auth-provider", () => ({
  useAuth: () => ({
    phase: "authenticated",
    backendUser: { id: "user-1" }
  })
}));

vi.mock("@/hooks/use-polling-resource", () => ({
  usePollingResource: () => ({
    data: {
      job_id: "job-1",
      source_filename: "invoice.pdf",
      source_file_size_bytes: 2516582,
      status: "completed",
      document_type: "invoice",
      current_stage: "completion_persisted",
      submitted_at: "2026-04-08T12:00:00Z",
      processing_started_at: "2026-04-08T12:01:00Z",
      completed_at: "2026-04-08T12:02:00Z",
      failed_at: null,
      output_ready: true,
      failure_message: null,
      download_available: true,
      timeline: [
        { stage: "upload_received", label: "Upload received", state: "completed" },
        { stage: "completion_persisted", label: "Completed", state: "completed" }
      ],
      extraction: {
        schema_version: "2026-04-08",
        document_type: "invoice",
        text_preview: "Invoice extraction summary",
        tables: [],
        images: [],
        normalized_json: {
          document_type: "invoice",
          invoice_number: "INV-1001"
        },
        extracted_json: {},
        validation_passed: true,
        validation_errors: []
      }
    },
    loading: false,
    error: null,
    refresh: vi.fn()
  })
}));

vi.mock("@/lib/api/client", () => ({
  downloadJobOutput: (...args: unknown[]) => downloadJobOutput(...args),
  downloadJobJson: (...args: unknown[]) => downloadJobJson(...args),
  getJobDetail: vi.fn()
}));

vi.mock("@/lib/download", () => ({
  triggerBrowserDownload: (...args: unknown[]) => triggerBrowserDownload(...args)
}));

describe("JobDetailPage", () => {
  beforeEach(() => {
    downloadJobOutput.mockReset();
    downloadJobJson.mockReset();
    triggerBrowserDownload.mockReset();
    writeClipboard.mockReset();
    downloadJobOutput.mockResolvedValue(new Blob(["excel"], { type: "application/octet-stream" }));
    downloadJobJson.mockResolvedValue(new Blob(["json"], { type: "application/json" }));
    writeClipboard.mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      configurable: true,
      value: { writeText: (...args: unknown[]) => writeClipboard(...args) }
    });
  });

  it("shows the completed download action and triggers the browser download", async () => {
    const user = userEvent.setup();

    render(<JobDetailPage params={{ jobId: "job-1" }} />);
    await user.click(screen.getByRole("button", { name: "Download All" }));

    expect(downloadJobOutput).toHaveBeenCalledWith("job-1");
    expect(triggerBrowserDownload).toHaveBeenCalled();
  });

  it("shows an honest empty state when no images are extracted", async () => {
    const user = userEvent.setup();

    render(<JobDetailPage params={{ jobId: "job-1" }} />);
    await user.click(screen.getByRole("tab", { name: "IMAGES" }));

    expect(screen.getByText("No images were extracted from this PDF.")).toBeInTheDocument();
    expect(screen.queryByText("image_1.png")).not.toBeInTheDocument();
  });

  it("supports download and copy actions for JSON output", async () => {
    const user = userEvent.setup();

    render(<JobDetailPage params={{ jobId: "job-1" }} />);
    await user.click(screen.getByRole("tab", { name: "JSON" }));
    await user.click(screen.getByRole("button", { name: "Download JSON" }));
    await user.click(screen.getByRole("button", { name: "Copy JSON" }));
    await screen.findByText("JSON copied to clipboard.");

    expect(downloadJobJson).toHaveBeenCalledWith("job-1");
    expect(triggerBrowserDownload).toHaveBeenCalled();
  });
});
