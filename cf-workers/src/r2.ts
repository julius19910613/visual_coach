import type { Bindings } from "./env";

const MAX_SIZE = 500 * 1024 * 1024; // 500MB

export async function readVideoAsBase64(env: Bindings, key: string): Promise<{ data: string; mimeType: string }> {
  const obj = await env.VISUAL_COACH.get(key);
  if (!obj) throw new Error(`R2 object not found: ${key}`);
  if (obj.size > MAX_SIZE) throw new Error(`Video too large: ${obj.size} bytes (max ${MAX_SIZE})`);

  const arrayBuf = await obj.arrayBuffer();
  const base64 = arrayBufferToBase64(arrayBuf);
  const mimeType = obj.httpMetadata?.contentType ?? inferMimeType(key);
  return { data: base64, mimeType };
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 8192;
  for (let i = 0; i < bytes.length; i += chunkSize) {
    const chunk = bytes.subarray(i, Math.min(i + chunkSize, bytes.length));
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
}

function inferMimeType(key: string): string {
  const ext = key.split(".").pop()?.toLowerCase();
  const map: Record<string, string> = {
    mp4: "video/mp4",
    mov: "video/quicktime",
    avi: "video/x-msvideo",
    mkv: "video/x-matroska",
    webm: "video/webm",
  };
  return map[ext ?? ""] ?? "video/mp4";
}
