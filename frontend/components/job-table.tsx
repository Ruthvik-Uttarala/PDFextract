import Link from "next/link";

import { formatTimestamp } from "@/lib/format";
import type { JobSummary } from "@/lib/types";

import { StatusBadge } from "@/components/status-badge";

export function JobTable({
  jobs,
  adminView = false
}: {
  jobs: JobSummary[];
  adminView?: boolean;
}) {
  if (jobs.length === 0) {
    return <p className="empty-copy">No jobs to show yet.</p>;
  }

  return (
    <div className="table-scroll">
      <table className="jobs-table">
        <thead>
          <tr>
            <th>File</th>
            <th>Status</th>
            <th>Submitted</th>
            <th>Document Type</th>
            {adminView ? <th>User</th> : null}
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => {
            const href = adminView ? `/admin/jobs/${job.job_id}` : `/jobs/${job.job_id}`;

            return (
              <tr key={job.job_id}>
                <td>
                  <div className="jobs-table__primary">
                    <Link href={href} className="text-link">
                      {job.source_filename}
                    </Link>
                  </div>
                  {job.failure_message ? (
                    <p className="jobs-table__meta jobs-table__meta--error">{job.failure_message}</p>
                  ) : null}
                </td>
                <td>
                  <StatusBadge status={job.status} />
                </td>
                <td>{formatTimestamp(job.submitted_at)}</td>
                <td>{job.document_type || "Pending"}</td>
                {adminView ? <td>{job.user_id || "Unknown"}</td> : null}
                <td>
                  <Link href={href} className="button button--ghost button--small">
                    View
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
