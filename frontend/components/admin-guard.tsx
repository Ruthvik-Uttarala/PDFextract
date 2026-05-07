"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/providers/auth-provider";

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const auth = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (auth.phase === "authenticated" && auth.backendUser?.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [auth.backendUser?.role, auth.phase, router]);

  if (auth.phase !== "authenticated") {
    return null;
  }

  if (auth.backendUser?.role !== "admin") {
    return null;
  }

  return <>{children}</>;
}
