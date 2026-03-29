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
