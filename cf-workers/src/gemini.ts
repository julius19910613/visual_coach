import type { Bindings } from "./env";
import type { PlayerAnalysisReport } from "./analyzer";
import { SYSTEM_INSTRUCTION, USER_PROMPT, RESPONSE_SCHEMA } from "./prompts";

export async function analyzeVideo(
  env: Bindings,
  videoBase64: string,
  mimeType: string,
): Promise<PlayerAnalysisReport> {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${env.GEMINI_API_KEY}`;

  const body = {
    system_instruction: { parts: [{ text: SYSTEM_INSTRUCTION }] },
    contents: [
      {
        parts: [
          { inline_data: { mime_type: mimeType, data: videoBase64 } },
          { text: USER_PROMPT },
        ],
      },
    ],
    generationConfig: {
      responseMimeType: "application/json",
      responseSchema: RESPONSE_SCHEMA,
    },
  };

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Gemini API error ${res.status}: ${text}`);
  }

  const json = (await res.json()) as any;
  const text = json.candidates?.[0]?.content?.parts?.[0]?.text as string | undefined;
  if (!text) throw new Error("Empty response from Gemini");

  return JSON.parse(text) as PlayerAnalysisReport;
}
