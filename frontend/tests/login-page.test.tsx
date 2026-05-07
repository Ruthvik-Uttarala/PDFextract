import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import LoginPage from "@/app/login/page";

const replace = vi.fn();
const signInWithGoogle = vi.fn(async () => undefined);

type AuthState = {
  phase: "loading" | "unauthenticated" | "authenticated" | "config-missing" | "error";
  missingKeys: string[];
  errorMessage: string | null;
  signInWithGoogle: () => Promise<void>;
};

let authState: AuthState = {
  phase: "unauthenticated",
  missingKeys: [],
  errorMessage: null,
  signInWithGoogle
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
    signInWithGoogle.mockClear();
    authState = {
      phase: "unauthenticated",
      missingKeys: [],
      errorMessage: null,
      signInWithGoogle
    };
  });

  it("starts Firebase Google sign-in from the login screen", async () => {
    const user = userEvent.setup();

    render(<LoginPage />);
    await user.click(screen.getByRole("button", { name: "Continue with Google" }));

    expect(signInWithGoogle).toHaveBeenCalledTimes(1);
  });
});
