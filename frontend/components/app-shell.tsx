"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/providers/auth-provider";

const primaryNav = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/upload", label: "Upload" },
  { href: "/jobs", label: "Jobs" }
] as const;

export function AppShell({ children, requiresAdmin = false }: { children: React.ReactNode; requiresAdmin?: boolean }) {
  const auth = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (auth.phase === "unauthenticated") {
      router.replace("/login");
      return;
    }

    if (
      auth.phase === "authenticated" &&
      requiresAdmin &&
      auth.backendUser?.role !== "admin"
    ) {
      router.replace("/dashboard");
    }
  }, [auth.backendUser?.role, auth.phase, requiresAdmin, router]);

  if (auth.phase === "loading") {
    return <AuthStateScreen title="Checking session" body="Loading your workspace." />;
  }

  if (auth.phase === "config-missing") {
    return (
      <AuthStateScreen
        title="Firebase configuration missing"
        body={`Missing public keys: ${auth.missingKeys.join(", ")}`}
      />
    );
  }

  if (auth.phase === "error") {
    return (
      <AuthStateScreen
        title="Backend session unavailable"
        body={auth.errorMessage || "The app could not load your backend session."}
        action={
          <button className="button button--primary" onClick={() => void auth.refreshSession()}>
            Retry
          </button>
        }
      />
    );
  }

  if (auth.phase !== "authenticated" || !auth.backendUser) {
    return <AuthStateScreen title="Redirecting" body="Taking you to sign in." />;
  }

  if (requiresAdmin && auth.backendUser.role !== "admin") {
    return <AuthStateScreen title="Admin access only" body="This route is limited to operators." />;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="app-header__eyebrow">PDFextract</p>
          <h1 className="app-header__title">Document processing workspace</h1>
        </div>
        <div className="app-header__actions">
          <div className="user-chip">
            <span>{auth.backendUser.display_name || auth.backendUser.email || "User"}</span>
            <span className="user-chip__role">{auth.backendUser.role}</span>
          </div>
          <button className="button button--secondary" onClick={() => void auth.signOutUser()}>
            Sign out
          </button>
        </div>
      </header>

      <nav className="primary-nav" aria-label="Primary">
        {primaryNav.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={pathname?.startsWith(item.href) ? "primary-nav__link is-active" : "primary-nav__link"}
          >
            {item.label}
          </Link>
        ))}
        {auth.backendUser.role === "admin" ? (
          <Link
            href="/admin/jobs"
            className={pathname?.startsWith("/admin/jobs") ? "primary-nav__link is-active" : "primary-nav__link"}
          >
            Admin
          </Link>
        ) : null}
      </nav>

      <main className="page-shell">{children}</main>
    </div>
  );
}

function AuthStateScreen({
  title,
  body,
  action
}: {
  title: string;
  body: string;
  action?: React.ReactNode;
}) {
  return (
    <main className="auth-screen">
      <section className="auth-card">
        <p className="auth-card__eyebrow">PDFextract</p>
        <h2 className="auth-card__title">{title}</h2>
        <p className="auth-card__body">{body}</p>
        {action ? <div className="auth-card__actions">{action}</div> : null}
      </section>
    </main>
  );
}
