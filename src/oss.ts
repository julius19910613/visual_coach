import { TosClient } from '@volcengine/tos-sdk';

function createTosClient() {
  return new TosClient({
    accessKeyId: process.env.TOS_ACCESS_KEY_ID!,
    accessKeySecret: process.env.TOS_ACCESS_KEY_SECRET!,
    region: process.env.TOS_REGION || 'cn-beijing',
    endpoint: process.env.TOS_ENDPOINT || 'tos-cn-beijing.volces.com',
    bucket: process.env.TOS_BUCKET || 'visual-coach',
  });
}

export async function getVideoBuffer(key: string): Promise<{ data: Buffer; mimeType: string }> {
  const client = createTosClient();
  const result = await client.getObject({ key });
  // getObject returns { data: Buffer, ... }
  const buf = Buffer.isBuffer(result.data) ? result.data : Buffer.from(result.data as any);
  return { data: buf, mimeType: inferMimeType(key) };
}

export async function getVideoPresignedUrl(key: string, expires: number = 3600): Promise<string> {
  const client = createTosClient();
  return client.getPreSignedUrl({ key, expires });
}

export async function getHeadObject(key: string) {
  const client = createTosClient();
  return client.headObject({ key });
}

export function inferMimeType(key: string): string {
  const ext = key.split('.').pop()?.toLowerCase();
  const map: Record<string, string> = {
    mp4: 'video/mp4',
    mov: 'video/quicktime',
    avi: 'video/x-msvideo',
    mkv: 'video/x-matroska',
    webm: 'video/webm',
  };
  return map[ext ?? ''] ?? 'video/mp4';
}
