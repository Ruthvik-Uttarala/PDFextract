import type { JobStatus } from "@/lib/types";

export function formatTimestamp(value: string | null): string {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatStatusLabel(status: JobStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}
