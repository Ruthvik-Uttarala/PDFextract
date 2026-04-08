import { FirebaseBootstrapCard } from "@/components/firebase-bootstrap-card";

export default function LoginPage() {
  return (
    <main className="shell">
      <div className="shell__content">
        <p className="shell__eyebrow">PDFextract Foundation</p>
        <h1 className="shell__title">Truthful Phase 0 and Phase 1 scaffold</h1>
        <p className="shell__subtitle">
          This Vercel-safe frontend only proves the local runtime foundation. It does
          not claim upload, job processing, or completed MVP behavior yet.
        </p>

        <div className="panel-grid">
          <section className="panel">
            <h2>Current scope</h2>
            <p>
              The frontend is intentionally thin in this phase. The canonical docs bind
              the stack, route discipline, and Firebase client integration path before
              product screens are implemented.
            </p>
            <ul className="list">
              <li>Next.js 14.2.25 App Router scaffold</li>
              <li>TypeScript 5.6.3 strict mode</li>
              <li>Firebase client env loading and initialization path</li>
              <li>Vercel-compatible deploy surface rooted in the monorepo</li>
            </ul>
          </section>

          <FirebaseBootstrapCard />
        </div>
      </div>
    </main>
  );
}
