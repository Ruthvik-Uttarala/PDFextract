"use client";

import { getApp, getApps, initializeApp, type FirebaseApp } from "firebase/app";
import {
  GoogleAuthProvider,
  browserLocalPersistence,
  getAuth,
  setPersistence,
  type Auth
} from "firebase/auth";

import { getFirebaseClientConfigStatus } from "@/lib/env";

let persistenceConfigured = false;

export function ensureFirebaseApp(): FirebaseApp {
  const status = getFirebaseClientConfigStatus();
  if (!status.ready || !status.config) {
    throw new Error(`Missing Firebase public environment variables: ${status.missingKeys.join(", ")}`);
  }

  return getApps().length > 0 ? getApp() : initializeApp(status.config);
}

export async function getFirebaseAuth(): Promise<Auth> {
  const auth = getAuth(ensureFirebaseApp());
  if (!persistenceConfigured) {
    await setPersistence(auth, browserLocalPersistence);
    persistenceConfigured = true;
  }
  return auth;
}

export function createGoogleProvider(): GoogleAuthProvider {
  const provider = new GoogleAuthProvider();
  provider.setCustomParameters({ prompt: "select_account" });
  return provider;
}
