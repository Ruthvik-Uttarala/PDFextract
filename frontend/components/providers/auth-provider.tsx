"use client";

import {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useState,
  type ReactNode
} from "react";

import { getCurrentUser } from "@/lib/api/client";
import { getApiBaseUrlStatus } from "@/lib/env";
import type { UserProfile } from "@/lib/types";

type AuthPhase = "loading" | "unauthenticated" | "authenticated" | "error";

type AuthContextValue = {
  phase: AuthPhase;
  backendUser: UserProfile | null;
  missingKeys: string[];
  errorMessage: string | null;
  continueToDemo: () => Promise<void>;
  signOutUser: () => Promise<void>;
  refreshSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);
const DEMO_SESSION_KEY = "pdfextract-demo-session";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<AuthPhase>("loading");
  const [backendUser, setBackendUser] = useState<UserProfile | null>(null);
  const [missingKeys, setMissingKeys] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const apiStatus = getApiBaseUrlStatus();
    const missingKeys = [...apiStatus.missingKeys];
    if (missingKeys.length > 0) {
      setPhase("error");
      setMissingKeys(missingKeys);
      setErrorMessage(`Missing public keys: ${missingKeys.join(", ")}`);
      return () => undefined;
    }

    const hasSession =
      typeof window !== "undefined" && window.localStorage.getItem(DEMO_SESSION_KEY) === "active";
    if (!hasSession) {
      startTransition(() => {
        setBackendUser(null);
        setErrorMessage(null);
        setPhase("unauthenticated");
      });
      return () => undefined;
    }

    void refreshSession();
    return () => undefined;
  }, []);

  async function syncBackendProfile(): Promise<void> {
    try {
      const profile = await getCurrentUser();
      startTransition(() => {
        setBackendUser(profile);
        setErrorMessage(null);
        setPhase("authenticated");
      });
    } catch (error) {
      startTransition(() => {
        setBackendUser(null);
        setErrorMessage(error instanceof Error ? error.message : "Backend session sync failed.");
        setPhase("error");
      });
    }
  }

  async function continueToDemo(): Promise<void> {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(DEMO_SESSION_KEY, "active");
    }
    startTransition(() => {
      setPhase("loading");
    });
    await syncBackendProfile();
  }

  async function signOutUser(): Promise<void> {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(DEMO_SESSION_KEY);
    }
    startTransition(() => {
      setBackendUser(null);
      setErrorMessage(null);
      setPhase("unauthenticated");
    });
  }

  async function refreshSession(): Promise<void> {
    const hasSession =
      typeof window !== "undefined" && window.localStorage.getItem(DEMO_SESSION_KEY) === "active";
    if (!hasSession) {
      startTransition(() => {
        setBackendUser(null);
        setErrorMessage(null);
        setPhase("unauthenticated");
      });
      return;
    }
    startTransition(() => {
      setPhase("loading");
    });
    await syncBackendProfile();
  }

  const value: AuthContextValue = {
    phase,
    backendUser,
    missingKeys,
    errorMessage,
    continueToDemo,
    signOutUser,
    refreshSession
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}
