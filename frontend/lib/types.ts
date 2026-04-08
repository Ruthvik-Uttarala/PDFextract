export type UserProfile = {
  id: string;
  firebase_uid: string;
  email: string | null;
  display_name: string | null;
  role: "user" | "admin";
  is_active: boolean;
};

export type JobStatus = "queued" | "processing" | "completed" | "failed";

export type JobTimelineItem = {
  stage: string;
  label: string;
  state: "pending" | "current" | "completed" | "failed";
};

export type JobSummary = {
  job_id: string;
  source_filename: string;
  status: JobStatus;
  document_type: string | null;
  current_stage: string | null;
  submitted_at: string;
  processing_started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  output_ready: boolean;
  failure_message: string | null;
  user_id?: string;
};

export type JobDetail = JobSummary & {
  timeline: JobTimelineItem[];
  download_available: boolean;
};

export type ProcessingAttempt = {
  processing_attempt_id: string;
  attempt_number: number;
  trigger_type: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  worker_request_id: string | null;
  failure_code: string | null;
  failure_message: string | null;
};

export type AdminAction = {
  admin_action_id: string;
  admin_user_id: string;
  action_type: string;
  notes: string | null;
  created_at: string;
};

export type AdminJobDetail = JobDetail & {
  failure_code: string | null;
  attempts: ProcessingAttempt[];
  admin_actions: AdminAction[];
  storage: {
    source_file_id: string | null;
    current_output_file_record_id: string | null;
    current_output_storage_key: string | null;
  };
  retry: {
    retry_allowed: boolean;
    reason: string | null;
    attempt_count: number;
    retry_limit: number | null;
  };
};
