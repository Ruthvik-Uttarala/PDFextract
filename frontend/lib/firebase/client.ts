'use client';

import { getApp, getApps, initializeApp, type FirebaseApp } from 'firebase/app';

import { getFirebaseClientConfigStatus } from '@/lib/env';

type BootstrapMissingState = Readonly<{
  status: 'missing';
  missingKeys: string[];
}>;

type BootstrapReadyState = Readonly<{
  status: 'ready';
  app: FirebaseApp;
}>;

type BootstrapErrorState = Readonly<{
  status: 'error';
  message: string;
}>;

type BootstrapCheckingState = Readonly<{
  status: 'checking';
}>;

export type FirebaseBootstrapState =
  | BootstrapCheckingState
  | BootstrapMissingState
  | BootstrapReadyState
  | BootstrapErrorState;

export function ensureFirebaseApp(): FirebaseBootstrapState {
  try {
    const status = getFirebaseClientConfigStatus();

    if (!status.ready || !status.config) {
      return {
        status: 'missing',
        missingKeys: status.missingKeys
      };
    }

    const app = getApps().length > 0 ? getApp() : initializeApp(status.config);

    return {
      status: 'ready',
      app
    };
  } catch (error) {
    return {
      status: 'error',
      message: error instanceof Error ? error.message : 'Unknown Firebase bootstrap error'
    };
  }
}
