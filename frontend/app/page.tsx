"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/providers/auth-provider";

export default function HomePage() {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (auth.phase === "authenticated") {
      router.replace("/dashboard");
      return;
    }

    if (auth.phase === "unauthenticated" || auth.phase === "config-missing" || auth.phase === "error") {
      router.replace("/login");
    }
  }, [auth.phase, router]);

  return (
    <main className="auth-screen">
      <section className="auth-card">
        <p className="auth-card__eyebrow">PDFextract</p>
        <h1 className="auth-card__title">Resolving your session</h1>
        <p className="auth-card__body">Checking whether to send you to login or the dashboard.</p>
      </section>
    </main>
  );
}
