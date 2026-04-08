import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import UploadPage from "@/app/(workspace)/upload/page";

const push = vi.fn();
const uploadPdf = vi.fn();

type AuthState = {
  getAccessToken: () => Promise<string | null>;
};

const authState: AuthState = {
  getAccessToken: async () => "user-token"
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push
  })
}));

vi.mock("@/components/providers/auth-provider", () => ({
  useAuth: () => authState
}));

vi.mock("@/lib/api/client", () => ({
  uploadPdf: (...args: unknown[]) => uploadPdf(...args)
}));

describe("UploadPage", () => {
  beforeEach(() => {
    push.mockReset();
    uploadPdf.mockReset();
    uploadPdf.mockResolvedValue({ job_id: "job-123" });
  });

  it("uploads one PDF and routes to the new job detail page", async () => {
    const user = userEvent.setup();
    const file = new File(["%PDF-1.4 mock pdf"], "invoice.pdf", { type: "application/pdf" });

    render(<UploadPage />);

    await user.upload(screen.getByLabelText(/drop a pdf here or browse/i), file);
    await user.click(screen.getByRole("button", { name: "Upload PDF" }));

    expect(uploadPdf).toHaveBeenCalledWith("user-token", file);
    expect(push).toHaveBeenCalledWith("/jobs/job-123");
  });
});
