import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/login/page";

const replace = vi.fn();
const continueToDemo = vi.fn(async () => undefined);

type AuthState = {
  phase: "loading" | "unauthenticated" | "authenticated" | "error";
  missingKeys: string[];
  errorMessage: string | null;
  continueToDemo: () => Promise<void>;
};

let authState: AuthState = {
  phase: "unauthenticated",
  missingKeys: [],
  errorMessage: null,
  continueToDemo
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace
  })
}));

vi.mock("@/components/providers/auth-provider", () => ({
  useAuth: () => authState
}));

describe("LoginPage", () => {
  beforeEach(() => {
    replace.mockReset();
    continueToDemo.mockClear();
    authState = {
      phase: "unauthenticated",
      missingKeys: [],
      errorMessage: null,
      continueToDemo
    };
  });

  it("starts demo access from the login screen", async () => {
    const user = userEvent.setup();

    render(<LoginPage />);
    await user.click(screen.getByRole("button", { name: "Continue to PDFextract" }));

    expect(continueToDemo).toHaveBeenCalledTimes(1);
  });
});
