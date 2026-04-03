# Visual Coach

篮球球员视频分析 API。上传比赛/训练视频，AI 自动分析进攻和防守表现。

部署在 [Tencent EdgeOne Pages](https://pages.edgeone.ai/) 平台上。

## 技术栈

- **Hono** - Web 框架
- **EdgeOne Pages Cloud Functions** - Serverless 运行时
- **豆包 API** (Doubao Seed 2.0 Pro) - 视频理解
- **火山引擎 TOS** - 视频存储

## 本地开发

```bash
# 1. 全局安装 EdgeOne CLI
npm install -g edgeone

# 2. 登录 EdgeOne
edgeone login

# 3. 安装项目依赖
npm install

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际的 API Key 和 TOS 配置

# 5. 启动本地开发服务器
npm run dev
# 服务运行在 http://localhost:8088

# 6. 测试
curl http://localhost:8088/api/health
```

## 部署

```bash
# 生产环境部署
npm run deploy

# 预览环境部署
npm run deploy:preview
```

### 环境变量管理

```bash
# 查看控制台中的环境变量
edgeone pages env ls

# 拉取控制台环境变量到本地
edgeone pages env pull

# 添加环境变量
edgeone pages env add ARK_API_KEY your_api_key

# 删除环境变量
edgeone pages env rm ARK_API_KEY
```

## API 接口

### `GET /api/health`
健康检查。

### `GET /api/`
API 信息。

### `POST /api/analyze`
分析视频。

**请求体 (JSON):**
```json
{ "r2_object_key": "黑队/highlight_大哥.mov" }
```

**请求体 (Form Data):**
```
r2_object_key=黑队/highlight_大哥.mov
```

**响应:**
```json
{
  "status": "completed",
  "result": {
    "player_summary": "...",
    "content_focus": "offensive",
    "dimensions": { "offense": {...}, "defense": {...} },
    "improvements": ["..."]
  }
}
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ARK_API_KEY` | 豆包 API Key | - |
| `TOS_REGION` | 火山引擎 TOS 区域 | `cn-beijing` |
| `TOS_ENDPOINT` | TOS Endpoint | `tos-cn-beijing.volces.com` |
| `TOS_ACCESS_KEY_ID` | AccessKey ID | - |
| `TOS_ACCESS_KEY_SECRET` | AccessKey Secret | - |
| `TOS_BUCKET` | TOS Bucket 名称 | `visual-coach` |

## 项目结构

```
visual-coach/
├── cloud-functions/
│   └── api/
│       └── [[default]].ts   # Hono 应用入口 (处理所有 /api/* 路由)
├── src/
│   ├── analyzer.ts           # 类型定义
│   ├── doubao.ts             # 豆包 API 调用
│   ├── oss.ts                # 火山引擎 TOS 存储
│   └── prompts.ts            # AI 提示词
├── edgeone.json              # EdgeOne 项目配置
├── package.json              # 项目配置
└── tsconfig.json             # TypeScript 配置
```
