import { Hono } from "hono";
import { cors } from "hono/cors";
import type { Bindings } from "./env";
import { createJob, getJob, updateJob, type Job } from "./job-store";
import { readVideoAsBase64 } from "./r2";
import { analyzeVideo } from "./gemini";

const app = new Hono<{ Bindings: Bindings }>();

app.use("*", cors());

app.get("/", (c) =>
  c.json({
    name: "Visual Coach API",
    version: "2.0.0",
    description: "Async player video analysis using Google Gemini API (Cloudflare Workers)",
    endpoints: [
      { method: "POST", path: "/api/analyze", description: "Create async analysis job from R2 object key" },
      { method: "GET", path: "/api/analyze/{job_id}", description: "Get async analysis job status" },
    ],
  }),
);

app.get("/health", (c) => c.json({ status: "ok", version: "2.0.0" }));

app.post("/api/analyze", async (c) => {
  const contentType = c.req.header("content-type") ?? "";

  let r2ObjectKey: string | undefined;

  if (contentType.includes("multipart/form-data")) {
    const form = await c.req.formData();
    r2ObjectKey = form.get("r2_object_key")?.toString();
  } else if (contentType.includes("application/x-www-form-urlencoded")) {
    const params = await c.req.parseBody();
    r2ObjectKey = params["r2_object_key"]?.toString();
  } else {
    const body = await c.req.json<{ r2_object_key?: string }>();
    r2ObjectKey = body.r2_object_key;
  }

  if (!r2ObjectKey) {
    return c.json({ error: "BadRequest", detail: "Provide 'r2_object_key'." }, 400);
  }

  const jobId = crypto.randomUUID();
  const job = await createJob(c.env.JOB_STORE, jobId, r2ObjectKey);

  // Fire-and-forget processing via waitUntil
  c.executionCtx.waitUntil(processJob(c.env, job));

  return c.json({ job_id: jobId, status: "pending" }, 202);
});

app.get("/api/analyze/:job_id", async (c) => {
  const jobId = c.req.param("job_id");
  const job = await getJob(c.env.JOB_STORE, jobId);
  if (!job) return c.json({ error: "NotFound", detail: "Job not found" }, 404);
  return c.json({
    job_id: job.id,
    status: job.status,
    error: job.error ?? null,
    result: job.result ?? null,
  });
});

async function processJob(env: Bindings, job: Job): Promise<void> {
  try {
    job.status = "processing";
    await updateJob(env.JOB_STORE, job);

    const { data, mimeType } = await readVideoAsBase64(env, job.r2_object_key);
    const result = await analyzeVideo(env, data, mimeType);

    job.status = "completed";
    job.result = result;
    await updateJob(env.JOB_STORE, job);
  } catch (err) {
    job.status = "failed";
    job.error = err instanceof Error ? err.message : String(err);
    await updateJob(env.JOB_STORE, job);
  }
}

export default app;
