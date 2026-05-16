# Pandai Plus - ComfyUI AI 增强套件

增强版 Pandai ComfyUI 节点，集成 LLM 对话、人物一致性、剧情分镜、图生图等 AI 功能。

---

## ✨ 功能概览

### 🤖 LLM 对话
- 可配置任意 OpenAI 兼容 API（DeepSeek/OpenAI/Ollama/vLLM等）
- 多轮对话历史管理（滑动窗口）
- 思考模式开关

### 👤 人物一致性
- 人物外貌锚点：定义角色外观，保持多图一致
- 多人物合并：支持多人场景
- 角色描述自动注入 prompt

### 📖 剧情分镜
- 将酒馆/SillyTavern 长剧情自动拆分成多个场景
- 每个场景自动生成图片 prompt
- 支持批量输出

### 🖼️ 图生图
- 图片分析：用视觉 LLM 分析图片内容/风格/人物
- 图生图 Prompt：基于参考图生成 img2img prompt
- 风格迁移：将一张图的风格应用到另一张

---

## 📦 安装

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Liuxd-1230/pandai-plus.git
pip install openai requests
```

---

## 🔧 全部节点

### Config 配置类

| 节点 | 输入 | 输出 | 说明 |
|------|------|------|------|
| Pandai API 配置 | api_url, api_key, default_model | api_config, default_model | API 连接配置 |
| Pandai API 测试 | api_config, test_mode | test_result, models_list | 测试连通性，获取模型列表 |

### Character 人物类

| 节点 | 输入 | 输出 | 说明 |
|------|------|------|------|
| Pandai 人物外貌锚点 | name, gender, age, appearance... | character_list, character_prompt | 定义单个角色 |
| Pandai 人物合并 | character_list_1, character_list_2... | merged_characters, merged_prompt | 合并多个角色 |

### LLM 对话类

| 节点 | 输入 | 输出 | 说明 |
|------|------|------|------|
| Pandai LLM 对话 | api_config, model, prompts, history... | response, thinking, chat_history | 主对话节点 |
| Pandai 历史清空 | trigger | empty_history | 清空历史 |
| Pandai 历史查看 | chat_history | history_text, total_messages | 查看历史 |

### Story 剧情分镜类

| 节点 | 输入 | 输出 | 说明 |
|------|------|------|------|
| Pandai 剧情分镜 | api_config, story_text, split_mode | scene_list, scene_summary | 长文本拆分场景 |
| Pandai 场景选择 | scene_list, scene_index | visual_prompt, scene_title... | 选择指定场景 |
| Pandai 场景列表查看 | scene_list | scenes_text, total_scenes | 查看所有场景 |
| Pandai 批量Prompt输出 | scene_list, separator | all_prompts, prompts_only | 批量输出prompt |

### Image 图片处理类

| 节点 | 输入 | 输出 | 说明 |
|------|------|------|------|
| Pandai 图片分析 | api_config, image, analysis_mode | analysis, extracted_prompt | 分析图片内容/风格 |
| Pandai 图生图Prompt | api_config, reference_analysis, user_request | img2img_prompt, negative_prompt | 生成img2img提示词 |
| Pandai 风格迁移Prompt | content_description, style_description | transfer_prompt, negative_prompt | 风格迁移提示词 |

---

## 🔗 工作流示例

### 1. 基础对话
```
[API 配置] ──> [LLM 对话] ──> response
```

### 2. 人物一致性生图
```
[API 配置] ──────────────┐
[人物锚点: 小红] ────────┼──> [LLM 对话] ──> 图片prompt
(user: "画她站在海边")    │
```

### 3. 剧情分镜（酒馆剧情 → 一组图片）
```
[酒馆剧情文本] ─story_text──> [剧情分镜] ─scene_list──> [场景选择]
                                                         │
                                      scene_index: 0 ────┘
                                                         │
                                                         ▼
                                                visual_prompt ──> 生图
```

### 4. 图生图（保持风格换人物）
```
[参考图片] ──> [图片分析] ─analysis──> [图生图Prompt] ──> img2img生图
                                       ▲
[人物锚点] ─character_list─────────────┘
```

### 5. 风格迁移
```
[内容图] ──> [图片分析] ──> content_description ──┐
                                                  ├──> [风格迁移Prompt] ──> 生图
[风格图] ──> [图片分析] ──> style_description ────┘
```

### 6. 多轮对话（带历史）
```
第一轮: [LLM 对话] ──chat_history──> 暂存
                        │
第二轮: [LLM 对话] ◄────┘ ──chat_history──> 暂存
                                    │
第三轮: [LLM 对话] ◄────────────────┘
```

---

## ⚙️ 关键参数说明

### character_prompt_mode（角色提示词注入位置）
| 选项 | 说明 |
|------|------|
| `prepend_to_user` | **推荐**，加在用户输入前面 |
| `prepend_to_system` | 加在系统提示词前面 |
| `append_to_user` | 加在用户输入后面 |

### history_mode（历史记录模式）
| 选项 | 说明 |
|------|------|
| `sliding_window` | **推荐**，只保留最近N轮，避免token超限 |
| `full` | 保留全部对话 |
| `none` | 不使用历史，每次新对话 |

### split_mode（剧情分割模式）
| 选项 | 说明 |
|------|------|
| `scene` | **推荐**，按场景分割 |
| `shot` | 按镜头分割（更细） |
| `beat` | 按节奏点分割 |

### analysis_mode（图片分析模式）
| 选项 | 说明 |
|------|------|
| `describe` | 通用描述 |
| `prompt` | 生成图片prompt |
| `style` | 提取艺术风格 |
| `character` | 提取人物外貌 |

---

## 📖 详细文档

- [USAGE_GUIDE.md](USAGE_GUIDE.md) - LLM对话、人物锚点使用指南
- [STORY_SPLITTER_GUIDE.md](STORY_SPLITTER_GUIDE.md) - 剧情分镜详细说明

---

## 🆚 对比原版

| 功能 | 原版 | Plus |
|------|------|------|
| API 配置 | 硬编码 DeepSeek | 可配置任意 OpenAI 兼容 API |
| API 测试 | 无 | 测试连通性 + 获取模型列表 |
| 人物一致性 | 无 | 多人物外貌锚点 |
| 历史管理 | 简单列表 | 滑动窗口 + 查看/清空 |
| 模型选择 | 固定下拉框 | 自由输入 |
| 剧情分镜 | 无 | 自动拆分长剧情 |
| 图片分析 | 无 | 视觉LLM分析 |
| 图生图 | 无 | img2img prompt生成 |
| 风格迁移 | 无 | 风格迁移prompt |
| 思考模式 | 无 | 可选开启 |

---

## 🎯 适用场景

- **AI 绘画工作流**：从文字描述到图片生成的完整流程
- **角色一致性**：同一角色多张图片保持外观一致
- **故事可视化**：将小说/剧本自动转化为分镜图
- **风格参考**：基于参考图生成相似风格的新图
- **酒馆/SillyTavern**：将角色扮演剧情转化为图片

---

## License

MIT
