import OSS from 'ali-oss';

function createOssClient() {
  return new OSS({
    region: process.env.OSS_REGION || 'oss-cn-shanghai',
    accessKeyId: process.env.OSS_ACCESS_KEY_ID!,
    accessKeySecret: process.env.OSS_ACCESS_KEY_SECRET!,
    bucket: process.env.OSS_BUCKET || 'visual-coach',
  });
}

export async function getVideoBuffer(key: string): Promise<{ data: Buffer; mimeType: string }> {
  const client = createOssClient();
  const result = await client.get(key);
  return { data: result.content as Buffer, mimeType: inferMimeType(key) };
}

export async function getVideoPresignedUrl(key: string, expires: number = 3600): Promise<string> {
  const client = createOssClient();
  return client.signatureUrl(key, { expires, response: { 'content-type': inferMimeType(key) } });
}

export async function getHeadObject(key: string) {
  const client = createOssClient();
  return client.head(key);
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
