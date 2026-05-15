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
      router.replace("/upload");
    }
  }, [auth.phase, router]);

  async function handleContinue(): Promise<void> {
    try {
      setSubmitting(true);
      await auth.continueToDemo();
      router.replace("/upload");
    } finally {
      setSubmitting(false);
    }
  }

  const isDisabled = submitting || auth.phase === "loading";

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <p className="auth-card__eyebrow">PDFextract</p>
        <h1 className="auth-card__title">Open the MVP workspace</h1>
        <p className="auth-card__body">
          Enter the demo flow to upload one PDF, track processing, and download the Excel output
          when it is ready.
        </p>

        <div className="auth-card__stack">
          <button
            className="button button--primary button--wide"
            disabled={isDisabled}
            onClick={() => void handleContinue()}
          >
            {submitting ? "Continuing..." : "Continue to PDFextract"}
          </button>
          <p className="helper-copy">This demo access mode is for MVP testing.</p>
        </div>

        {auth.phase === "error" ? (
          <div className="notice notice--error">
            <strong>Session setup is unavailable.</strong>
            <p>{auth.errorMessage || "Unable to start the demo session."}</p>
          </div>
        ) : null}
      </section>
    </main>
  );
}
