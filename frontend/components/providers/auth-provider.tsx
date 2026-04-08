"use client";

import {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useState,
  type ReactNode
} from "react";
import {
  onAuthStateChanged,
  signInWithPopup,
  signOut,
  type User as FirebaseUser
} from "firebase/auth";

import { getCurrentUser } from "@/lib/api/client";
import { getFirebaseClientConfigStatus } from "@/lib/env";
import { createGoogleProvider, getFirebaseAuth } from "@/lib/firebase/client";
import type { UserProfile } from "@/lib/types";

type AuthPhase = "loading" | "unauthenticated" | "authenticated" | "config-missing" | "error";

type AuthContextValue = {
  phase: AuthPhase;
  firebaseUser: FirebaseUser | null;
  backendUser: UserProfile | null;
  missingKeys: string[];
  errorMessage: string | null;
  signInWithGoogle: () => Promise<void>;
  signOutUser: () => Promise<void>;
  getAccessToken: () => Promise<string | null>;
  refreshSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [phase, setPhase] = useState<AuthPhase>("loading");
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [backendUser, setBackendUser] = useState<UserProfile | null>(null);
  const [missingKeys, setMissingKeys] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const status = getFirebaseClientConfigStatus();
    if (!status.ready) {
      setPhase("config-missing");
      setMissingKeys(status.missingKeys);
      return () => undefined;
    }

    let isCancelled = false;
    let unsubscribe: (() => void) | undefined;

    void (async () => {
      try {
        const auth = await getFirebaseAuth();
        unsubscribe = onAuthStateChanged(auth, (user) => {
          if (isCancelled) {
            return;
          }

          if (!user) {
            startTransition(() => {
              setFirebaseUser(null);
              setBackendUser(null);
              setErrorMessage(null);
              setPhase("unauthenticated");
            });
            return;
          }

          startTransition(() => {
            setPhase("loading");
            setFirebaseUser(user);
          });
          void syncBackendProfile(user);
        });
      } catch (error) {
        if (isCancelled) {
          return;
        }
        startTransition(() => {
          setErrorMessage(
            error instanceof Error ? error.message : "Firebase authentication could not start."
          );
          setPhase("error");
        });
      }
    })();

    return () => {
      isCancelled = true;
      unsubscribe?.();
    };
  }, []);

  async function syncBackendProfile(user: FirebaseUser): Promise<void> {
    try {
      const token = await user.getIdToken();
      const profile = await getCurrentUser(token);
      startTransition(() => {
        setBackendUser(profile);
        setErrorMessage(null);
        setPhase("authenticated");
      });
    } catch (error) {
      startTransition(() => {
        setBackendUser(null);
        setErrorMessage(error instanceof Error ? error.message : "Backend session sync failed.");
        setPhase("error");
      });
    }
  }

  async function signInWithGoogle(): Promise<void> {
    const auth = await getFirebaseAuth();
    await signInWithPopup(auth, createGoogleProvider());
  }

  async function signOutUser(): Promise<void> {
    const auth = await getFirebaseAuth();
    await signOut(auth);
  }

  async function getAccessToken(): Promise<string | null> {
    const auth = await getFirebaseAuth();
    const currentUser = auth.currentUser;
    if (!currentUser) {
      return null;
    }
    return currentUser.getIdToken();
  }

  async function refreshSession(): Promise<void> {
    const auth = await getFirebaseAuth();
    if (!auth.currentUser) {
      startTransition(() => {
        setBackendUser(null);
        setPhase("unauthenticated");
      });
      return;
    }
    startTransition(() => {
      setPhase("loading");
    });
    await syncBackendProfile(auth.currentUser);
  }

  const value: AuthContextValue = {
    phase,
    firebaseUser,
    backendUser,
    missingKeys,
    errorMessage,
    signInWithGoogle,
    signOutUser,
    getAccessToken,
    refreshSession
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return value;
}
