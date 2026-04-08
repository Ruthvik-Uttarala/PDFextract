import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import JobDetailPage from "@/app/(workspace)/jobs/[jobId]/page";

const downloadJobOutput = vi.fn();
const triggerBrowserDownload = vi.fn();

vi.mock("@/components/providers/auth-provider", () => ({
  useAuth: () => ({
    phase: "authenticated",
    backendUser: { id: "user-1" },
    getAccessToken: async () => "user-token"
  })
}));

vi.mock("@/hooks/use-polling-resource", () => ({
  usePollingResource: () => ({
    data: {
      job_id: "job-1",
      source_filename: "invoice.pdf",
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
      ]
    },
    loading: false,
    error: null,
    refresh: vi.fn()
  })
}));

vi.mock("@/lib/api/client", () => ({
  downloadJobOutput: (...args: unknown[]) => downloadJobOutput(...args),
  getJobDetail: vi.fn()
}));

vi.mock("@/lib/download", () => ({
  triggerBrowserDownload: (...args: unknown[]) => triggerBrowserDownload(...args)
}));

describe("JobDetailPage", () => {
  beforeEach(() => {
    downloadJobOutput.mockReset();
    triggerBrowserDownload.mockReset();
    downloadJobOutput.mockResolvedValue(new Blob(["excel"], { type: "application/octet-stream" }));
  });

  it("shows the completed download action and triggers the browser download", async () => {
    const user = userEvent.setup();

    render(<JobDetailPage params={{ jobId: "job-1" }} />);
    await user.click(screen.getByRole("button", { name: "Download Excel" }));

    expect(downloadJobOutput).toHaveBeenCalledWith("user-token", "job-1");
    expect(triggerBrowserDownload).toHaveBeenCalled();
  });
});
