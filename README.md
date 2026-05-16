# Pandai Plus - ComfyUI LLM Integration

增强版的 Pandai ComfyUI 节点，支持可配置的 API、人物一致性锚点、改进的多轮对话。

## 新增功能

### 1. 可配置的 API 设置
- **API Config 节点**: 配置 API URL 和 API Key
- **API Test 节点**: 测试 API 连通性、获取可用模型列表

### 2. 人物外貌锚点 (Character Anchor)
- 定义角色外貌描述，保持多张图片生成的一致性
- 支持多人物场景
- 可选择锚点注入方式（system prompt / user prompt）

### 3. 改进的多轮对话
- 滑动窗口历史管理，避免 token 超限
- 历史记录查看/清空节点
- 更清晰的数据流

## 节点说明

### Config 类节点

| 节点 | 说明 |
|------|------|
| Pandai API Config | 配置 API URL 和 Key |
| Pandai API Test | 测试连通性和获取模型列表 |

### Character 类节点

| 节点 | 说明 |
|------|------|
| Pandai Character Anchor | 定义单个角色外貌 |
| Pandai Character Merge | 合并多个角色列表 |

### LLM 类节点

| 节点 | 说明 |
|------|------|
| Pandai LLM Chat | 主对话节点，支持角色锚点和历史 |
| Pandai History Clear | 清空历史记录 |
| Pandai History View | 查看历史记录内容 |

## 使用示例

### 基础对话流程
```
API Config -> LLM Chat -> Response
```

### 带角色锚点的生图 Prompt 生成
```
API Config ──────────────────┐
Character Anchor ────────────┼──> LLM Chat --> Response
(user_prompt: "画一张她站在海边的图") 
```

### 多人物场景
```
Character Anchor (Alice) ─┐
                          ├─> Character Merge ──> LLM Chat
Character Anchor (Bob) ───┘
```

### 带历史的多轮对话
```
API Config ─────────────────┐
History ────────────────────┼──> LLM Chat ──┬──> Response
(user_prompt: "继续")                         └──> History (连到下一轮)
```

## API 兼容性

支持 OpenAI 兼容的 API：
- DeepSeek
- OpenAI
- 本地部署的 Ollama / vLLM / LM Studio
- 其他兼容 OpenAI 格式的 API

### 本地 Ollama 示例
- API URL: `http://localhost:11434`
- Model: `llama3`, `qwen2`, etc.

## 安装

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/YOUR_USERNAME/pandai-plus.git
pip install openai requests
```

## 对比原版

| 功能 | 原版 | Plus |
|------|------|------|
| API 配置 | 硬编码 DeepSeek | 可配置任意 OpenAI 兼容 API |
| API 测试 | 无 | 测试连通性 + 获取模型列表 |
| 人物一致性 | 无 | 多人物外貌锚点 |
| 历史管理 | 简单列表 | 滑动窗口 + 查看/清空 |
| 模型选择 | 固定列表 | 自由输入 |

## License

MIT
