export const SYSTEM_INSTRUCTION = `你是专业篮球分析师。你正在分析一段球员比赛或训练视频。

视频可能以进攻为主或以防守为主。请遵守以下规则：

1. **仅根据实际出现在画面中的内容评分**，切勿臆测画面外或未展示的内容。
2. 某维度若几乎无相关镜头（例如视频全是进攻画面、没有防守镜头），将 score 设为 null，observability 设为 "none"，notes 中说明「画面中无/极少XX镜头，无法评估」。
3. observability 含义：
   - "full"：有足够画面可做出全面评估
   - "partial"：有部分画面，但不足以全面评估（此时 score 可给分或为 null，视情况而定）
   - "none"：几乎没有相关画面，无法评估，score 必须为 null
4. 进攻维度关注：运球、传球、投篮、突破、跑位、挡拆、篮板、决策等。
5. 防守维度关注：盯人、协防、抢断、盖帽、篮板卡位、站位、补防等。
6. 输出语言为中文。所有 notes、player_summary、improvements 均使用中文。
7. 输出必须严格符合给定的 JSON Schema，不要添加额外字段。`;

export const USER_PROMPT = `请分析该球员视频。

视频可能偏进攻或偏防守。对每个维度（offense、defense）：
- 若有足够画面，则评分(1-5)、设置 observability 为 "full" 或 "partial"，并给出 notes 和 highlights；
- 若无相关画面，则 score 设为 null，observability 设为 "none"，notes 说明原因（如「画面中无防守镜头，无法评估」）。

content_focus 根据视频实际内容填写：若多为进攻则 "offensive"，多为防守则 "defensive"，两者均衡则 "balanced"。

请输出严格符合给定 JSON Schema 的 JSON。`;

export const RESPONSE_SCHEMA = {
  type: "object",
  properties: {
    player_summary: { type: "string", description: "One-sentence overall evaluation of the player's performance" },
    content_focus: { type: "string", enum: ["offensive", "defensive", "balanced"], description: "Whether the video is mainly offensive, defensive, or balanced" },
    dimensions: {
      type: "object",
      properties: {
        offense: {
          type: "object",
          properties: {
            score: { type: ["integer", "null"], description: "Score 1-5 if enough footage; null when observability is none" },
            observability: { type: "string", enum: ["full", "partial", "none"] },
            notes: { type: "string" },
            highlights: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  timestamp: { type: "string", description: "Time in MM:SS format" },
                  description: { type: "string" },
                },
                required: ["timestamp", "description"],
              },
            },
          },
          required: ["observability", "notes", "highlights"],
        },
        defense: {
          type: "object",
          properties: {
            score: { type: ["integer", "null"], description: "Score 1-5 if enough footage; null when observability is none" },
            observability: { type: "string", enum: ["full", "partial", "none"] },
            notes: { type: "string" },
            highlights: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  timestamp: { type: "string", description: "Time in MM:SS format" },
                  description: { type: "string" },
                },
                required: ["timestamp", "description"],
              },
            },
          },
          required: ["observability", "notes", "highlights"],
        },
      },
      required: ["offense", "defense"],
    },
    improvements: {
      type: "array",
      items: { type: "string" },
      description: "Actionable improvement suggestions",
    },
  },
  required: ["player_summary", "content_focus", "dimensions", "improvements"],
};
