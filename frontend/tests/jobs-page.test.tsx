import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import JobsPage from "@/app/(workspace)/jobs/page";

const listJobs = vi.fn();

vi.mock("@/components/providers/auth-provider", () => ({
  useAuth: () => ({
    phase: "authenticated",
    backendUser: { id: "user-1" },
    getAccessToken: async () => "user-token"
  })
}));

vi.mock("@/hooks/use-polling-resource", () => ({
  usePollingResource: () => ({
    data: [
      {
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
        failure_message: null
      }
    ],
    loading: false,
    error: null,
    refresh: vi.fn()
  })
}));

vi.mock("@/lib/api/client", () => ({
  listJobs: (...args: unknown[]) => listJobs(...args)
}));

describe("JobsPage", () => {
  beforeEach(() => {
    listJobs.mockReset();
  });

  it("renders the newest-first jobs history from the backend data", () => {
    render(<JobsPage />);

    expect(screen.getByRole("heading", { name: "Your full processing history" })).toBeInTheDocument();
    expect(screen.getByText("invoice.pdf")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });
});
