'use client';

import { useEffect, useState } from 'react';

import {
  ensureFirebaseApp,
  type FirebaseBootstrapState
} from '@/lib/firebase/client';

const initialState: FirebaseBootstrapState = {
  status: 'checking'
};

export function FirebaseBootstrap() {
  const [state, setState] = useState<FirebaseBootstrapState>(initialState);

  useEffect(() => {
    setState(ensureFirebaseApp());
  }, []);

  return (
    <aside className="bootstrap-banner" aria-live="polite">
      <span className={`bootstrap-banner__pill ${state.status}`}>
        Firebase bootstrap
      </span>
      {state.status === 'ready' ? (
        <p>Browser Firebase app initialized.</p>
      ) : state.status === 'missing' ? (
        <p>Waiting on public Firebase env values before initialization.</p>
      ) : state.status === 'error' ? (
        <p>Firebase bootstrap failed: {state.message}</p>
      ) : (
        <p>Checking browser Firebase configuration.</p>
      )}
    </aside>
  );
}
