"use client";

import { useEffect, useState } from "react";

import {
  getFirebaseClientApp,
  getFirebaseClientConfigStatus,
  type FirebaseClientConfigStatus
} from "@/lib/firebase-client";

export function FirebaseBootstrapCard() {
  const [status, setStatus] = useState<FirebaseClientConfigStatus>(() =>
    getFirebaseClientConfigStatus()
  );

  useEffect(() => {
    const nextStatus = getFirebaseClientConfigStatus();
    if (!nextStatus.configured) {
      setStatus(nextStatus);
      return;
    }

    try {
      getFirebaseClientApp();
      setStatus({
        ...nextStatus,
        initialized: true
      });
    } catch (error) {
      setStatus({
        ...nextStatus,
        initialized: false,
        error:
          error instanceof Error
            ? error.message
            : "Firebase client initialization failed."
      });
    }
  }, []);

  const badgeClassName = !status.configured
    ? "status status--warn"
    : status.initialized
      ? "status status--ok"
      : "status status--error";

  const badgeLabel = !status.configured
    ? "Config Missing"
    : status.initialized
      ? "Client Ready"
      : "Init Failed";

  return (
    <section className="panel">
      <h2>Firebase client path</h2>
      <div className={badgeClassName}>{badgeLabel}</div>
      <p>
        The browser-side Firebase bootstrap lives in <code>frontend/lib/firebase-client.ts</code>.
        This page executes that path directly when the public env shape is complete.
      </p>

      {!status.configured ? (
        <>
          <p>Missing public env keys:</p>
          <ul className="list">
            {status.missing.map((key) => (
              <li key={key}>{key}</li>
            ))}
          </ul>
        </>
      ) : null}

      {status.error ? <p className="status status--error">{status.error}</p> : null}

      <div className="code-block">
        <strong>Expected env file:</strong>
        <br />
        <code>frontend/.env.example</code>
      </div>
    </section>
  );
}
