"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/components/providers/auth-provider";

type NavigationItem = {
  href: string;
  label: string;
  icon: string;
  available: boolean;
};

function buildNavigationItems(isAdmin: boolean): NavigationItem[] {
  const items: NavigationItem[] = [
    { href: "/upload", label: "Upload", icon: "U", available: true },
    { href: "/jobs", label: "My Files", icon: "F", available: true },
    { href: "/dashboard", label: "History", icon: "H", available: true },
    { href: "#", label: "Settings", icon: "S", available: false },
    { href: "#", label: "Help", icon: "?", available: false },
  ];

  if (isAdmin) {
    items.push({ href: "/admin/jobs", label: "Admin", icon: "A", available: true });
  }

  return items;
}

export function AppShell({
  children,
  requiresAdmin = false,
}: {
  children: React.ReactNode;
  requiresAdmin?: boolean;
}) {
  const auth = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    if (auth.phase === "unauthenticated") {
      router.replace("/login");
      return;
    }

    if (auth.phase === "authenticated" && requiresAdmin && auth.backendUser?.role !== "admin") {
      router.replace("/dashboard");
    }
  }, [auth.backendUser?.role, auth.phase, requiresAdmin, router]);

  if (auth.phase === "loading") {
    return <AuthStateScreen title="Checking session" body="Loading your workspace." />;
  }

  if (auth.phase === "config-missing") {
    return (
      <AuthStateScreen
        title="Configuration missing"
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

  const navigationItems = buildNavigationItems(auth.backendUser.role === "admin");

  return (
    <div className="workspace-shell">
      <aside className="workspace-sidebar" aria-label="Main sidebar">
        <div className="workspace-brand">
          <span className="workspace-brand__icon">P</span>
          <div>
            <p className="workspace-brand__title">PDF Extract</p>
            <p className="workspace-brand__subtitle">Utility</p>
          </div>
        </div>

        <nav className="workspace-nav">
          {navigationItems.map((item) => {
            if (!item.available) {
              return (
                <span key={item.label} className="workspace-nav__item is-disabled">
                  <span className="workspace-nav__icon">{item.icon}</span>
                  <span>{item.label}</span>
                </span>
              );
            }

            const isActive = item.href !== "#" && pathname?.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={isActive ? "workspace-nav__item is-active" : "workspace-nav__item"}
              >
                <span className="workspace-nav__icon">{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="workspace-user">
          <div className="workspace-user__avatar">
            {(auth.backendUser.display_name || auth.backendUser.email || "U").slice(0, 1).toUpperCase()}
          </div>
          <div className="workspace-user__details">
            <p>{auth.backendUser.display_name || "Signed-in user"}</p>
            <span>{auth.backendUser.email || "No email available"}</span>
          </div>
          <button className="button button--ghost button--small" onClick={() => void auth.signOutUser()}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="workspace-content">{children}</main>
    </div>
  );
}

function AuthStateScreen({
  title,
  body,
  action,
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
