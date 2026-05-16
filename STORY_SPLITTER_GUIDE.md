# 剧情分镜功能使用说明

## 功能简介

将酒馆/SillyTavern等角色扮演工具输出的长剧情，自动拆分成多个图片场景，每个场景生成对应的图片prompt。

---

## 节点说明

| 节点 | 功能 |
|------|------|
| Pandai 剧情分镜 | 将长文本拆分成多个场景，输出场景列表 |
| Pandai 场景选择 | 从场景列表中选择指定序号的场景 |
| Pandai 场景列表查看 | 查看所有场景的详细信息 |
| Pandai 批量Prompt输出 | 一次性输出所有场景的prompt |

---

## 使用流程

### 方式一：逐个场景生成（推荐）

```
[API 配置] ────────────────────────────┐
                                       │
[人物锚点] (可选) ─character_list──┐   │
                                   │   │
[剧情文本]                         │   │
    │                              ▼   ▼
    └──story_text──> [剧情分镜] ─scene_list──> [场景选择] ─visual_prompt──> [LLM对话/生图]
                                              │
                                              └──scene_index: 0 (第一张)
                                                 scene_index: 1 (第二张)
                                                 scene_index: 2 (第三张)
                                                 ...
```

**工作流程：**
1. 粘贴酒馆输出的剧情到 `story_text`
2. 剧情分镜节点自动拆分成多个场景
3. 场景选择节点选择第几个场景（index从0开始）
4. 输出的 `visual_prompt` 可以直接用于生图

---

### 方式二：批量输出所有Prompt

```
[剧情分镜] ─scene_list──> [批量Prompt输出] ──> 复制所有prompt
                                              │
                                              └──prompts_only (纯prompt，方便批量粘贴)
```

输出格式：
```
Characters: 小红: young adult female, 黑色长发...

a young woman standing at the harbor, sunset, wind blowing hair
---
Characters: 小红: young adult female, 黑色长发...

a young woman sitting in a coffee shop, reading a book, warm lighting
---
...
```

---

## 分割模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `scene` | 按场景分割 | **推荐**，每个场景是一个完整画面 |
| `shot` | 按镜头分割 | 更细粒度，包含特写/中景/远景 |
| `beat` | 按节奏点分割 | 适合有动作/情感转折的剧情 |

---

## 完整示例

### 输入（酒馆输出的剧情）：
```
清晨，小红从睡梦中醒来，阳光透过窗帘洒在她的脸上。她伸了个懒腰，从床上坐起来。

"又是新的一天呢..."她自言自语道。

洗漱完毕后，小红穿上了她最喜欢的红色连衣裙，对着镜子整理了一下黑色的长发。

出门后，她漫步在街道上，路过了常去的那家咖啡店。透过玻璃窗，她看到里面坐满了人。

"今天人真多啊。"她想着，决定去公园散步。

公园里，樱花正盛开。小红站在樱花树下，微风吹过，花瓣纷纷扬扬地落下。她闭上眼睛，享受着这一刻的宁静。
```

### 输出（自动拆分的场景）：
```
=== 剧情分镜 (5 个场景) ===

场景 1: Morning Awakening
  描述: 小红从睡梦中醒来，阳光洒在脸上
  镜头: close-up | 情绪: peaceful
  Prompt: a young woman waking up in bed, morning sunlight through curtains on face, stretching, sleepy expression, warm lighting

场景 2: Getting Dressed
  描述: 小红穿红色连衣裙，整理长发
  镜头: medium shot | 情绪: cheerful
  Prompt: a young woman with black long hair wearing red dress, looking at mirror, brushing hair, bedroom background, soft lighting

场景 3: Walking on Street
  描述: 小红漫步在街道上，经过咖啡店
  镜头: wide shot | 情绪: calm
  Prompt: a young woman in red dress walking on street, passing by a coffee shop with glass windows, city morning, natural lighting

场景 4: Crowded Coffee Shop
  描述: 透过玻璃窗看到咖啡店里坐满了人
  镜头: medium shot | 情绪: observing
  Prompt: view through coffee shop glass window, many customers inside, warm interior lighting, reflection of street outside

场景 5: Cherry Blossom Park
  描述: 小红站在樱花树下，花瓣纷飞
  镜头: wide shot | 情绪: serene
  Prompt: a young woman standing under cherry blossom tree, petals falling, eyes closed, peaceful expression, park setting, soft sunlight
```

---

## 参数详解

### max_scenes（最大场景数）
- 默认 8，范围 2-20
- 剧情越长可以设越大
- 太多可能导致每个场景太碎片化

### style_hint（风格提示）
可选，告诉AI你想要的图片风格：
- "anime style" - 动漫风格
- "realistic photography" - 写实摄影
- "cyberpunk" - 赛博朋克
- "watercolor painting" - 水彩画风
- "studio ghibli style" - 吉卜力风格

### character_list（角色列表）
连接人物锚点节点，AI会自动将角色外貌融入每个场景的prompt。

---

## 常见问题

### Q: 为什么拆分的场景不准确？
A: 可以尝试：
1. 换用更强的模型
2. 调整 `max_scenes` 数量
3. 尝试不同的 `split_mode`

### Q: 如何让所有场景的人物外貌一致？
A: 连接 `Pandai 人物外貌锚点` 节点到 `character_list` 输入。

### Q: 输出的prompt可以直接用吗？
A: 可以直接用于 Stable Diffusion / Midjourney 等。如果需要更详细的prompt，可以再接一个 LLM 节点进行润色。
