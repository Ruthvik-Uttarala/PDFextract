import { formatStatusLabel } from "@/lib/format";
import type { JobStatus } from "@/lib/types";

export function StatusBadge({ status }: { status: JobStatus }) {
  return (
    <span className={`status-badge status-badge--${status}`} aria-label={`Job status: ${status}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      {formatStatusLabel(status)}
    </span>
  );
}
