# Visual Coach — 球员视频分析

基于 Gemini API 的球员视频分析工具，支持本地视频文件输入，输出带进攻/防守维度的结构化分析报告。

## 安装

需要先安装 [uv](https://docs.astral.sh/uv/)。

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖并创建环境
uv sync

# 或手动激活虚拟环境后运行
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

## 配置

复制 `.env.example` 为 `.env`，填入 Gemini API Key（从 [Google AI Studio](https://aistudio.google.com/) 获取）：

```
GEMINI_API_KEY=your_api_key_here
```

## 使用

```bash
# 分析视频并输出到 stdout（uv 会自动确保依赖就绪）
uv run main.py path/to/player_video.mp4

# 保存报告到文件
uv run main.py path/to/player_video.mp4 -o report.json

# 美化 JSON 输出
uv run main.py path/to/player_video.mp4 --pretty
```

也可在激活 `.venv` 后直接使用 `python main.py`。

## 输出格式

报告为 JSON，包含：

- `player_summary`：一句话总体评价
- `content_focus`：视频侧重（offensive / defensive / balanced）
- `dimensions.offense` / `dimensions.defense`：进攻/防守分析，含 `score`、`observability`、`notes`、`highlights`
- `improvements`：改进建议列表

视频偏进攻时，防守维度若无足够画面会标记为 `observability: "none"`、`score: null`。

## Web API (Async, Vercel-friendly)

项目提供 FastAPI Web API，默认采用异步任务模式，适配 Vercel 部署（API 只负责任务提交与状态查询）。

### 启动 API 服务器

```bash
# 使用 uv 启动（推荐）
uv run run_api.py

# 或指定自定义端口和主机
uv run run_api.py --host 0.0.0.0 --port 8080

# 开发模式（自动重载）
uv run run_api.py --reload
```

服务器启动后：
- API 文档：http://localhost:8000/docs （Swagger UI）
- 根端点：http://localhost:8000/
- 健康检查：http://localhost:8000/health

### API 端点

#### POST /api/analyze

创建异步分析任务。

**请求格式**：`multipart/form-data`

**参数（三选一）**：
- `r2_object_key`：R2 对象 key（推荐，生产使用）
- `file`：保留兼容字段（异步模式下默认不处理）
- `video_url`：保留兼容字段（异步模式下默认不处理）

**响应**：
- `202`：任务已创建，返回 `{ "job_id": "...", "status": "pending" }`
- `400`：参数错误
- `500`：任务创建/入队失败

#### GET /api/analyze/{job_id}

查询异步任务状态：

- `pending | processing`：任务进行中
- `completed`：结果在 `result` 字段（`PlayerAnalysisReport`）
- `failed`：错误信息在 `error` 字段

**示例**：

```bash
# 1) 提交任务（推荐传 R2 key）
curl -X POST "http://localhost:8000/api/analyze" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "r2_object_key=videos/白队/highlight_高神.mov"

# 2) 查询任务状态
curl "http://localhost:8000/api/analyze/<job_id>"
```

### 测试 API

```bash
# 运行基本测试（健康检查、根端点）
uv run test_api.py

# Worker 服务（Cloud Run/本地）启动示例
uv run run_worker.py --port 8100
```

### Async 环境变量（部署重点）

在 `.env` 中配置：

```bash
ASYNC_MODE=true
WORKER_ENDPOINT=https://your-worker-host
WORKER_SHARED_SECRET=your_shared_secret
JOB_STORE_PATH=data/jobs.db
GEMINI_URL_MODEL=gemini-3-flash-preview
GEMINI_URL_MAX_BYTES=104857600
```

- `WORKER_ENDPOINT` 为空时，会退化为本地 inline 处理（仅适合开发，不建议 Vercel 生产使用）。

## MCP（Cursor）

项目已配置 [Google Developer Knowledge MCP](https://developers.google.com/knowledge/mcp)（官方远程服务），用于在 Cursor 中检索 Google 开发者文档（含 Google Cloud、Firebase、Android、Maps 等；与 Gemini / 视频 API 相关的官方说明也可通过文档检索辅助）。

1. 在 [Google Cloud Console](https://console.cloud.google.com/apis/library/developerknowledge.googleapis.com) 为项目启用 **Developer Knowledge API**。
2. 在 [凭据](https://console.cloud.google.com/apis/credentials) 中创建 API 密钥，并将 **API 限制** 设为仅 **Developer Knowledge API**（与 AI Studio 的 `GEMINI_API_KEY` 不同）。
3. （可选）启用远程 MCP：`gcloud beta services mcp enable developerknowledge.googleapis.com --project=YOUR_PROJECT_ID`
4. 在启动 Cursor 的终端环境中导出密钥，使 `${env:DEVELOPER_KNOWLEDGE_API_KEY}` 生效，例如：
   ```bash
   export DEVELOPER_KNOWLEDGE_API_KEY="你的_GCP_密钥"
   open -a Cursor /path/to/visual_coach
   ```
   或将 `export` 写入 `~/.zshrc` 后重启 Cursor。

配置位于 [.cursor/mcp.json](.cursor/mcp.json)。验证：在 Agent 中提问与 Google 文档相关的问题，应出现 `search_documents` / `get_documents` 工具调用。

## Cloudflare R2 存储（可选）

配置 R2 后，上传的视频会持久化存储，分析响应中会包含 `video_url` 字段。未配置时行为不变（仅使用临时文件）。

1. 在 [Cloudflare Dashboard](https://dash.cloudflare.com/) 创建 R2 存储桶。
2. 在 **R2 > 管理 R2 API 令牌** 中创建 API 令牌（权限：对象读写）。
3. 在 `.env` 中添加：

```
R2_ACCOUNT_ID=你的账户ID
R2_ACCESS_KEY_ID=你的Access Key ID
R2_SECRET_ACCESS_KEY=你的Secret Access Key
R2_BUCKET_NAME=visual-coach-videos
R2_PUBLIC_URL=                # 可选：自定义域名，如 https://videos.yourdomain.com
R2_KEY_PREFIX=videos          # 可选：R2 对象前缀，默认 videos
```

`R2_PUBLIC_URL` 为空时，API 返回的 `video_url` 为预签名 URL（默认 1 小时有效）；设置自定义域名后返回永久公开链接（需在 R2 存储桶设置中启用公开访问）。

### 白队 / 黑队 视频批量上传到 R2

如果你希望把本地 `白队`、`黑队` 目录下的所有视频同步到 R2，可以使用脚本：

```bash
uv run python scripts/upload_teams_to_r2.py          # 实际上传
uv run python scripts/upload_teams_to_r2.py --dry-run  # 仅查看将上传的对象 key
```

行为说明：
- 仅扫描项目根目录下的 `白队`、`黑队` 文件夹。
- 支持扩展名：.mp4/.mov/.avi/.webm/.mkv/.mpeg/.mpg/.flv/.wmv/.3gpp。
- R2 对象 key 形如：`videos/白队/xxx.mov`、`videos/黑队/yyy.mp4`（可通过 `R2_KEY_PREFIX` 调整 `videos`）。
- 同名 key 会被新文件**覆盖**（R2/S3 语义）。

> 注意：旧的上传脚本 `upload_to_r2.py`、`upload_wrangler.py` 与 `upload_wrangler.sh` 仅保留作历史参考，不再推荐使用（范围过大且包含硬编码配置）。\n> 建议在确认新脚本工作正常后，在 Cloudflare Dashboard 中**轮换 R2 API 密钥**，避免旧凭证泄露风险。
