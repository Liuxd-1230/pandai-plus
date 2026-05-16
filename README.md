# Pandai Plus - ComfyUI LLM Integration

增强版 Pandai ComfyUI 节点，支持可配置 API、人物一致性锚点、改进的多轮对话。

## ✨ 新增功能

### 1. 可配置 API
- **API 配置节点**: 自由设置 API URL 和 API Key
- **API 测试节点**: 一键测试连通性、获取可用模型列表
- 支持所有 OpenAI 兼容 API (DeepSeek/OpenAI/Ollama/vLLM等)

### 2. 人物外貌锚点 (Character Anchor)
- 定义角色外貌描述，保持多张图片生成的一致性
- 支持多人物场景
- 灵活的提示词注入方式

### 3. 改进的多轮对话
- 滑动窗口历史管理，避免 token 超限
- 历史记录查看/清空节点
- **正确连接 history 才能实现多轮对话！**

### 4. 思考模式
- 可选开启 AI 思考过程，更准确但更慢

---

## 📦 安装

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Liuxd-1230/pandai-plus.git
pip install openai requests
```

---

## 🔧 节点说明

| 节点 | 类别 | 说明 |
|------|------|------|
| Pandai API 配置 | Config | 设置 API URL/Key/默认模型 |
| Pandai API 测试 | Config | 测试连通性，获取模型列表 |
| Pandai 人物外貌锚点 | Character | 定义角色外观 |
| Pandai 人物合并 | Character | 合并多个角色列表 |
| Pandai LLM 对话 | LLM | 主对话节点 |
| Pandai 历史清空 | LLM | 清空历史记录 |
| Pandai 历史查看 | LLM | 查看历史内容 |

---

## 🔗 快速上手

### 基础对话
```
[API 配置] ──api_config──> [LLM 对话] ──> response
                └──default_model──> model
```

### 带历史的多轮对话
```
第一轮: [API 配置] ──> [LLM 对话] ──> response + chat_history
                                         │
第二轮: ──────────────────────────────────┘ ──> [LLM 对话] ──> response + chat_history
                                                                 │
第三轮: ──────────────────────────────────────────────────────────┘ ──> ...
```

### 人物一致性生图
```
[API 配置] ──────────────┐
[人物锚点: 小红] ────────┼──> [LLM 对话] ──> 图片prompt
(user: "画她站在海边")    │
```

---

## 📖 详细文档

- [使用指南](USAGE_GUIDE.md) - 参数说明、连接方式、常见问题

---

## 🆚 对比原版

| 功能 | 原版 | Plus |
|------|------|------|
| API 配置 | 硬编码 DeepSeek | 可配置任意 OpenAI 兼容 API |
| API 测试 | 无 | 测试连通性 + 获取模型列表 |
| 人物一致性 | 无 | 多人物外貌锚点 |
| 历史管理 | 简单列表 | 滑动窗口 + 查看/清空 |
| 模型选择 | 固定下拉框 | 自由输入 |
| 思考模式 | 无 | 可选开启 |

---

## License

MIT
