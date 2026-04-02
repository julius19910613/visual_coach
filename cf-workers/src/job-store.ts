export type JobStatus = "pending" | "processing" | "completed" | "failed";

export interface Job {
  id: string;
  status: JobStatus;
  r2_object_key: string;
  result?: unknown;
  error?: string;
  created_at: string;
  updated_at: string;
}

const KEY_PREFIX = "job:";

export async function createJob(kv: KVNamespace, id: string, r2ObjectKey: string): Promise<Job> {
  const now = new Date().toISOString();
  const job: Job = { id, status: "pending", r2_object_key: r2ObjectKey, created_at: now, updated_at: now };
  await kv.put(`${KEY_PREFIX}${id}`, JSON.stringify(job));
  return job;
}

export async function getJob(kv: KVNamespace, id: string): Promise<Job | null> {
  const raw = await kv.get(`${KEY_PREFIX}${id}`);
  if (!raw) return null;
  return JSON.parse(raw) as Job;
}

export async function updateJob(kv: KVNamespace, job: Job): Promise<void> {
  job.updated_at = new Date().toISOString();
  await kv.put(`${KEY_PREFIX}${job.id}`, JSON.stringify(job));
}
