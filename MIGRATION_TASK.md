# Visual Coach → Cloudflare Workers 迁移任务

## 项目概述
将篮球视频分析 API 从 Python/FastAPI/Vercel 迁移到 Cloudflare Workers。

## 原始项目
- 路径: `/Users/ppt/projects/visual_coach`
- 技术栈: Python + FastAPI + SQLite + boto3 + Gemini API
- 功能: 接收 R2 视频 object_key，下载视频，调用 Gemini 分析，返回分析报告

## 关键源文件（请阅读理解）
- `app/api/main.py` — FastAPI 路由和入口
- `src/gemini_client.py` — Gemini API 调用逻辑
- `src/analyzer.py` — 视频分析主逻辑
- `src/prompts.py` — 分析提示词模板
- `src/schemas.py` — 数据模型
- `src/r2_storage.py` — R2 存储操作
- `src/async_job_processor.py` — 异步任务处理
- `src/job_store.py` — 任务状态存储（SQLite）
- `config/settings.py` — 配置

## 目标架构
- Cloudflare Workers (TypeScript, Hono 框架)
- R2 原生绑定（无需 boto3）
- Workers KV 存储 job 状态（替代 SQLite）
- Gemini API REST 调用（fetch，无需 SDK）

## 核心设计决策

### 1. Gemini API 调用方式
Workers 内存只有 128MB，不能全量加载视频。方案：
- 使用 Gemini REST API 的 `generateContent` 端点
- 将视频从 R2 流式读取，分块（<128MB）传给 Gemini
- 或者如果视频 <128MB，一次性读取后用 inline_data 传给 Gemini
- 模型使用: `gemini-2.5-flash`

### 2. Job 状态存储
- 使用 Workers KV 替代 SQLite
- Key: `job:{job_id}`, Value: JSON（status, result, error）
- 或直接用内存 Map（简单，但 Worker 重启会丢失）

### 3. R2 访问
- Workers 原生绑定 R2 bucket
- 通过 `env.VISUAL_COACH.get(object_key)` 直接读取
- 无需 boto3、无需 presigned URL

### 4. API 接口（保持兼容）
- `GET /` — 健康检查/API 信息
- `GET /health` — 健康检查
- `POST /api/analyze` — 创建分析任务（接收 r2_object_key）
- `GET /api/analyze/{job_id}` — 查询任务状态

### 5. Wrangler 配置
```toml
name = "visual-coach"
main = "src/index.ts"
compatibility_date = "2024-12-01"

[[r2_buckets]]
binding = "VISUAL_COACH"
bucket_name = "visualcoach"

[kv_namespaces]
binding = "JOB_STORE"
id = "<需要创建>"
```

### 6. 环境变量（secrets）
- `GEMINI_API_KEY` — Gemini API 密钥
- R2 访问通过 binding，不需要 key

### 7. 分析流程
1. 接收 POST 请求，提取 `r2_object_key`
2. 创建 job（pending 状态），存入 KV
3. 从 R2 binding 读取视频数据
4. 将视频数据通过 Gemini REST API 发送分析
5. 解析 Gemini 返回的分析报告
6. 更新 job 状态为 completed/failed
7. 返回 job_id

**注意**: Workers 单次请求有 CPU 时间限制（免费 10ms，付费 30s），但 wall-clock 时间不限（等 I/O 不算 CPU）。视频分析流程中：
- R2 读取是 I/O（不算 CPU）
- fetch 调用 Gemini 是 I/O（不算 CPU）
- 解析 JSON 是 CPU

所以只要 JSON 解析不太重，单次请求就能完成整个流程。如果视频太大，可以分步骤处理。

## 执行步骤

1. **创建 `cf-workers/` 子目录**（在项目根目录下）
2. **初始化项目**: `npm init -y`, 安装 `hono`, `wrangler` devDependencies
3. **编写 TypeScript 代码**:
   - `src/index.ts` — Worker 入口
   - `src/routes.ts` — API 路由
   - `src/gemini.ts` — Gemini API 调用
   - `src/analyzer.ts` — 分析逻辑（复用 prompts.py 的提示词）
   - `src/r2.ts` — R2 读取
   - `src/job-store.ts` — KV job 存储
4. **创建 `wrangler.toml`** 配置文件
5. **创建 KV namespace**: `npx wrangler kv namespace create JOB_STORE`
6. **设置 secrets**: `npx wrangler secret put GEMINI_API_KEY`
7. **本地测试**: `npx wrangler dev` + curl 测试
8. **部署**: `npx wrangler deploy`
9. **线上测试**: 用 curl 调用线上 API，测试完整流程
10. **如有错误**: 修复后重新部署，最多重试 3 次

## 测试用例
```bash
# 健康检查
curl https://<worker-url>/health

# 创建分析任务
curl -X POST https://<worker-url>/api/analyze \
  -F "r2_object_key=videos/白队/highlight_Dao小帅.mov"

# 查询任务状态
curl https://<worker-url>/api/analyze/<job_id>
```

## 重要提示
- ⚠️ **绝对不要在代码中硬编码 API Key**
- 使用 `env.GEMINI_API_KEY` 从 secrets 读取
- R2 使用 binding `env.VISUAL_COACH`
- 测试时读取 `/Users/ppt/projects/visual_coach/.env` 获取 API Key（仅用于 `wrangler secret put`）
- 部署完成后运行: `openclaw system event --text "Done: Visual Coach Cloudflare Workers 部署完成" --mode now`
