import { getApp, getApps, initializeApp, type FirebaseApp } from "firebase/app";

const REQUIRED_PUBLIC_KEYS = [
  "NEXT_PUBLIC_FIREBASE_API_KEY",
  "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN",
  "NEXT_PUBLIC_FIREBASE_PROJECT_ID",
  "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET",
  "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID",
  "NEXT_PUBLIC_FIREBASE_APP_ID"
] as const;

export type FirebaseClientConfigStatus = {
  configured: boolean;
  initialized: boolean;
  missing: string[];
  error?: string;
};

export function getFirebaseClientConfigStatus(): FirebaseClientConfigStatus {
  const missing = REQUIRED_PUBLIC_KEYS.filter((key) => !process.env[key]);

  return {
    configured: missing.length === 0,
    initialized: false,
    missing
  };
}

export function getFirebaseClientApp(): FirebaseApp {
  const status = getFirebaseClientConfigStatus();

  if (!status.configured) {
    throw new Error(
      `Missing Firebase public environment variables: ${status.missing.join(", ")}`
    );
  }

  if (getApps().length > 0) {
    return getApp();
  }

  return initializeApp({
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID
  });
}
