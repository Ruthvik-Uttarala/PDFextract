type FirebaseClientConfig = {
  apiKey: string;
  authDomain: string;
  projectId: string;
  appId: string;
  messagingSenderId: string;
  storageBucket: string;
  measurementId?: string;
};

const requiredFirebaseKeys = {
  apiKey: "NEXT_PUBLIC_FIREBASE_API_KEY",
  authDomain: "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN",
  projectId: "NEXT_PUBLIC_FIREBASE_PROJECT_ID",
  appId: "NEXT_PUBLIC_FIREBASE_APP_ID",
  messagingSenderId: "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID",
  storageBucket: "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET"
} as const;

export type FirebaseClientConfigStatus = Readonly<{
  ready: boolean;
  missingKeys: string[];
  config: FirebaseClientConfig | null;
}>;

export type ApiBaseUrlStatus = Readonly<{
  ready: boolean;
  missingKeys: string[];
  baseUrl: string | null;
}>;

const localApiFallback = "http://127.0.0.1:8000";

export function getFirebaseClientConfigStatus(): FirebaseClientConfigStatus {
  const missingKeys = Object.values(requiredFirebaseKeys).filter((envKey) => !process.env[envKey]);
  const ready = missingKeys.length === 0;

  return {
    ready,
    missingKeys,
    config: ready
      ? {
          apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY as string,
          authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN as string,
          projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID as string,
          appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID as string,
          messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID as string,
          storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET as string,
          measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID || undefined
        }
      : null
  };
}

export function getApiBaseUrlStatus(): ApiBaseUrlStatus {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  if (configuredBaseUrl) {
    return {
      ready: true,
      missingKeys: [],
      baseUrl: configuredBaseUrl.replace(/\/$/, "")
    };
  }

  if (process.env.NODE_ENV === "production") {
    return {
      ready: false,
      missingKeys: ["NEXT_PUBLIC_API_BASE_URL"],
      baseUrl: null
    };
  }

  return {
    ready: true,
    missingKeys: [],
    baseUrl: localApiFallback
  };
}

export function getApiBaseUrl(): string {
  const status = getApiBaseUrlStatus();
  if (!status.ready || !status.baseUrl) {
    throw new Error(`Missing API public environment variables: ${status.missingKeys.join(", ")}`);
  }
  return status.baseUrl;
}
