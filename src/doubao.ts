import type { PlayerAnalysisReport } from './analyzer';
import { SYSTEM_INSTRUCTION, USER_PROMPT } from './prompts';

const DOUBAO_BASE = 'https://ark.cn-beijing.volces.com/api/v3';
const MODEL = 'doubao-seed-2-0-pro-260215';

/**
 * Analyze video using Doubao Responses API.
 * Small videos: base64 inline. Large videos: use provided presigned URL.
 */
export async function analyzeVideo(
  apiKey: string,
  videoData: Buffer | null,
  mimeType: string,
  videoUrl: string,
): Promise<PlayerAnalysisReport> {
  let finalVideoUrl: string;

  if (videoData) {
    const base64 = videoData.toString('base64');
    finalVideoUrl = `data:${mimeType};base64,${base64}`;
  } else {
    finalVideoUrl = videoUrl;
  }

  const url = `${DOUBAO_BASE}/responses`;
  const body = {
    model: MODEL,
    instructions: SYSTEM_INSTRUCTION,
    input: [
      {
        role: 'user',
        content: [
          { type: 'input_video', video_url: finalVideoUrl },
          { type: 'input_text', text: USER_PROMPT },
        ],
      },
    ],
  };

  console.log(`Calling Doubao API, video size: ${videoData ? `${videoData.length} bytes (inline)` : 'presigned URL'}`);

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Doubao API error ${res.status}: ${text}`);
  }

  const json = (await res.json()) as any;

  const outputs = json.output ?? [];
  const textBlock = outputs.find(
    (o: any) => o.type === 'message' && o.content?.[0]?.type === 'output_text',
  );
  const text: string | undefined = textBlock?.content?.[0]?.text;

  if (!text) {
    const raw = JSON.stringify(json);
    throw new Error(`Unexpected Doubao response format: ${raw.slice(0, 500)}`);
  }

  const cleaned = text.replace(/^```(?:json)?\s*\n?/m, '').replace(/\n?```\s*$/m, '').trim();
  return JSON.parse(cleaned) as PlayerAnalysisReport;
}
