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
  apiKey: 'NEXT_PUBLIC_FIREBASE_API_KEY',
  authDomain: 'NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN',
  projectId: 'NEXT_PUBLIC_FIREBASE_PROJECT_ID',
  appId: 'NEXT_PUBLIC_FIREBASE_APP_ID',
  messagingSenderId: 'NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID',
  storageBucket: 'NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET'
} as const;

export type FirebaseClientConfigStatus = Readonly<{
  ready: boolean;
  presentKeys: string[];
  missingKeys: string[];
  config: FirebaseClientConfig | null;
}>;

export function getFirebaseClientConfigStatus(): FirebaseClientConfigStatus {
  const resolved = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID,
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID,
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET,
    measurementId: process.env.NEXT_PUBLIC_FIREBASE_MEASUREMENT_ID
  } satisfies Record<string, string | undefined>;

  const presentKeys = Object.entries(requiredFirebaseKeys)
    .filter(([, envKey]) => Boolean(process.env[envKey]))
    .map(([, envKey]) => envKey);

  const missingKeys = Object.entries(requiredFirebaseKeys)
    .filter(([, envKey]) => !process.env[envKey])
    .map(([, envKey]) => envKey);

  const ready = missingKeys.length === 0;

  return {
    ready,
    presentKeys,
    missingKeys,
    config: ready
      ? {
          apiKey: resolved.apiKey as string,
          authDomain: resolved.authDomain as string,
          projectId: resolved.projectId as string,
          appId: resolved.appId as string,
          messagingSenderId: resolved.messagingSenderId as string,
          storageBucket: resolved.storageBucket as string,
          measurementId: resolved.measurementId || undefined
        }
      : null
  };
}
