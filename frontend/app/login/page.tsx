"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/providers/auth-provider";

export default function LoginPage() {
  const auth = useAuth();
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (auth.phase === "authenticated") {
      router.replace("/dashboard");
    }
  }, [auth.phase, router]);

  async function handleGoogleSignIn(): Promise<void> {
    try {
      setSubmitting(true);
      await auth.signInWithGoogle();
    } finally {
      setSubmitting(false);
    }
  }

  const isDisabled = submitting || auth.phase === "loading" || auth.phase === "config-missing";

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <p className="auth-card__eyebrow">PDFextract</p>
        <h1 className="auth-card__title">Sign in to start a new document job</h1>
        <p className="auth-card__body">
          Authenticate with Firebase, upload one PDF, track processing, and download the
          Excel output when it is ready.
        </p>

        <div className="auth-card__stack">
          <button className="button button--primary button--wide" disabled={isDisabled} onClick={() => void handleGoogleSignIn()}>
            {submitting ? "Signing in..." : "Continue with Google"}
          </button>
          <p className="helper-copy">Google sign-in is the only supported MVP login flow.</p>
        </div>

        {auth.phase === "config-missing" ? (
          <div className="notice notice--warning">
            <strong>Firebase configuration is incomplete.</strong>
            <p>Missing public keys: {auth.missingKeys.join(", ")}</p>
          </div>
        ) : null}

        {auth.phase === "error" && auth.errorMessage ? (
          <div className="notice notice--error">
            <strong>Authentication is unavailable.</strong>
            <p>{auth.errorMessage}</p>
          </div>
        ) : null}
      </section>
    </main>
  );
}
