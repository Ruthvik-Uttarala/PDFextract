"use client";

import { useCallback, useEffect, useState } from "react";

export function usePollingResource<T>({
  enabled,
  load,
  pollWhen,
  intervalMs = 5000,
  dependencies = []
}: {
  enabled: boolean;
  load: () => Promise<T>;
  pollWhen?: (value: T | null) => boolean;
  intervalMs?: number;
  dependencies?: readonly unknown[];
}) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(enabled);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const nextValue = await load();
      setData(nextValue);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Request failed.");
    } finally {
      setLoading(false);
    }
  }, [load]);

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    void refresh();
  }, [enabled, refresh, ...dependencies]);

  useEffect(() => {
    if (!enabled) {
      return;
    }

    if (pollWhen && !pollWhen(data)) {
      return;
    }

    const timer = window.setInterval(() => {
      void refresh();
    }, intervalMs);

    return () => {
      window.clearInterval(timer);
    };
  }, [data, enabled, intervalMs, pollWhen, refresh]);

  return { data, loading, error, refresh };
}
