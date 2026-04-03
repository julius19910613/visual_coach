import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { getVideoBuffer, getVideoPresignedUrl, getHeadObject, inferMimeType } from '../../src/oss';
import { analyzeVideo } from '../../src/doubao';

const BASE64_MAX_BYTES = 80 * 1024 * 1024; // 80MB

const app = new Hono();
app.use('*', cors());

app.get('/', (c) =>
  c.json({
    name: 'Visual Coach API',
    version: '5.0.0',
    description: 'Player video analysis using Doubao API + Volcengine TOS (EdgeOne Pages)',
  }),
);

app.get('/health', (c) => c.json({ status: 'ok', version: '5.0.0' }));

app.post('/analyze', async (c) => {
  const contentType = c.req.header('content-type') ?? '';
  let objectKey: string | undefined;

  if (contentType.includes('multipart/form-data')) {
    const form = await c.req.formData();
    objectKey = form.get('r2_object_key')?.toString();
  } else {
    const body = await c.req.json<{ r2_object_key?: string }>();
    objectKey = body.r2_object_key;
  }

  if (!objectKey) {
    return c.json({ error: 'BadRequest', detail: "Provide 'r2_object_key'." }, 400);
  }

  try {
    const headResult = await getHeadObject(objectKey);
    const fileSize = parseInt((headResult as any).data?.['content-length'] || '0') || 0;

    let videoData: Buffer | null = null;
    let videoUrl = '';
    const mimeType = inferMimeType(objectKey);

    if (fileSize <= BASE64_MAX_BYTES) {
      const { data } = await getVideoBuffer(objectKey);
      videoData = data;
    } else {
      videoUrl = await getVideoPresignedUrl(objectKey);
    }

    const apiKey = process.env.ARK_API_KEY!;
    const result = await analyzeVideo(apiKey, videoData, mimeType, videoUrl);
    return c.json({ status: 'completed', result });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return c.json({ status: 'failed', error: message }, 500);
  }
});

export default app;
