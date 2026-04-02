# Visual Coach

篮球球员视频分析 API。上传比赛/训练视频，AI 自动分析进攻和防守表现。

## 技术栈

- **Node.js** + **Hono** (Web 框架)
- **豆包 API** (Doubao Seed 2.0 Pro) - 视频理解
- **阿里云 OSS** - 视频存储

## 本地开发

```bash
# 1. 安装依赖
npm install

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入实际的 API Key 和 OSS 配置

# 3. 启动开发服务器
npm run dev

# 4. 测试
curl http://localhost:3000/health
```

## API 接口

### `GET /health`
健康检查。

### `GET /`
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
| `OSS_REGION` | 阿里云 OSS 区域 | `oss-cn-shanghai` |
| `OSS_ACCESS_KEY_ID` | 阿里云 AccessKey ID | - |
| `OSS_ACCESS_KEY_SECRET` | 阿里云 AccessKey Secret | - |
| `OSS_BUCKET` | OSS Bucket 名称 | `visual-coach` |
| `PORT` | 服务端口 | `3000` |

## 部署

阿里云函数计算 FC 3.0（自定义运行时），使用 `npm run build && npm start`。

## 项目结构

```
src/
├── analyzer.ts   # 类型定义
├── doubao.ts     # 豆包 API 调用
├── oss.ts        # 阿里云 OSS 存储
├── prompts.ts    # AI 提示词
├── index.ts      # Hono 路由
└── server.ts     # Node.js 入口
```
