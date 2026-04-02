# Visual Coach - Cloudflare Workers 版

视觉 Coach API

用于分析篮球球员视频，并将其转化为结构化的分析报告。

使用 Google Gemini API 进行视频分析。

原始项目是 Python (FastAPI) 项目，路径: /Users/ppt/projects/visual_coach

你需要将这个项目改造为 Cloudflare Workers 版本。

## 项目背景

- **原始项目**: Python (FastAPI + SQLite + boto3 + Gemini File API
- **目标**: 改为 TypeScript (Cloudflare Workers + R2 原生绑定 + D1 (Workers KV)
- **核心挑战**: Gemini File API 不支持从 R2 URL 直接加载视频。 Worker 内存限制 128MB)
 无法全量加载大内存

- Workers 内存限制:128MB,无法全量加载视频 → 顅须流式处理
- Workers 内存限制:128MB, 可能不够 → **方案 B: 将视频分块流式从 R2 下载到临时文件（然后以 Gemini URL 发送给分析)**

- 视频分块读取（ 分块大小 ≤ 128MB， 否则分步骤失败，提示错误)
- Worker 可返回分析失败信息，前端返回 job ID + 502 瓶待重试

如果失败则标记为失败)
- 如果失败, 用 AI 定时自动重新上传到 R2，并重试（最多3次)
- 如果重试耗尽, 用尽 R2 内存，用户自 "File too large" 的错误提示,不区分大小写一个占位符，让用户知道哪个步骤可以跳过
然后获取报告)

- **下载响应**: Worker 落 R2 分块下载,然后上传到 Gemini File API（使用 inline data，无需临时文件))
- **流式处理**: Worker 从 R2 流式读取视频数据（不做"上传)
Gemini API（使用 fetch 从 Gemini 服务器发送文件数据（内含 `r2_object_key`），请求体 JSON）
- Worker 运行时会从 `env.GEMINI_API_KEY` 跻加 Authorization头 `Authorization: "x-vercel-protection-bypass": token
- `wrangler secret deploy --production` 使用 `wrangler tail`5` 知道实际的部署 URL
 确认服务可用

用 Cloudflare Worker 請在日志中查看完整的请求和响应报告
- **最终测试**: 錙选 **简短视频做分析**测试（只要发现返回完整报告,调用 `wrangler tail`1` 悃部署日志中是否有错误

运行 `wrangler deploy --prod` 額fix问题并重新部署。 如果有错误， 并告诉我具体错误信息，我会手动修复并重试
最多3次)
- **测试完成后**: 用 curl 诃s 宏{测试报告的 胜利,https://部署的_url/api/analyze/{job_id}
- 检查 worker health 状态: 裁剪响应,读取 job store 知百内容
- 用 curl 聋s检查是否有错误: `wrangler tail`20` 查看 worker 最近的 deployments

- 用 `wrangler deployments list` 知道项目的部署 URL
- 用 curl 浤s worker 的真实 URL 发 GET响应,测试是否正确
- **重要**: 完成后将在代码中调用 `openclaw system event` 通知我完成:

 当完全完成后运行:
`openclaw system event --text "Done: visual coach Cloudflare Workers 部署完成" --mode now'`

openclaw system event --text "Done: Visual coach Cloudflare Workers deployed,使用 wrangler deploy --prod. Fix issues. 尔告诉我我错误信息，我会手动修复并重试,最多3次，- **测试完成后**: 用 curl 发送结果到飞书

报告)

