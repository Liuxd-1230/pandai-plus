import json
from typing import List, Dict, Tuple


# ============================================================
# 1. 剧情分割节点 - 把长文本拆分成多个场景
# ============================================================
class Pandai_Story_Splitter:
    """
    剧情分镜节点
    将酒馆/SillyTavern等输出的长剧情自动拆分成多个图片场景
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_config": ("API_CONFIG",),
                "model": ("STRING", {
                    "multiline": False,
                    "default": "deepseek-chat",
                }),
                "story_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "粘贴酒馆/角色扮演输出的长剧情..."
                }),
                "split_mode": (["scene", "shot", "beat"], {
                    "default": "scene",
                    "tooltip": "scene=按场景分割（推荐），shot=按镜头分割（更细），beat=按节奏点分割"
                }),
                "max_scenes": ("INT", {
                    "default": 8,
                    "min": 2,
                    "max": 20,
                    "step": 1,
                    "tooltip": "最多拆分成几个场景"
                }),
            },
            "optional": {
                "character_list": ("CHARACTER_LIST",),
                "style_hint": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "风格提示（可选），如：动漫风格，写实摄影，赛博朋克..."
                }),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "自定义系统提示词（留空使用内置默认）。用于控制LLM如何拆分场景和生成prompt，例如：强调特定画风、指定输出格式、加入质量标签等"
                }),
            }
        }

    RETURN_TYPES = ("SCENE_LIST", "STRING")
    RETURN_NAMES = ("scene_list", "scene_summary")
    FUNCTION = "split_story"
    CATEGORY = "Pandai/Story"

    def split_story(self, api_config, model, story_text, split_mode="scene",
                    max_scenes=8, character_list=None, style_hint="",
                    system_prompt=""):

        from openai import OpenAI

        api_url = api_config["api_url"]
        api_key = api_config["api_key"]

        if not model or model.strip() == "":
            model = api_config.get("default_model", "deepseek-chat")

        base_url = api_url if api_url.endswith("/v1") else f"{api_url}/v1"
        client = OpenAI(api_key=api_key, base_url=base_url)

        # 构建角色信息
        character_info = ""
        if character_list:
            char_parts = []
            for char in character_list:
                desc = f"- {char['name']}: {char['age']} {char['gender']}"
                if char['appearance']:
                    desc += f", {char['appearance']}"
                if char['clothing']:
                    desc += f", wearing {char['clothing']}"
                if char['features']:
                    desc += f", {char['features']}"
                char_parts.append(desc)
            character_info = "\n".join(char_parts)

        # 分割模式说明
        mode_desc = {
            "scene": "场景级分割 - 按地点/时间/氛围变化切分，每张图是一个完整场景",
            "shot": "镜头级分割 - 更细粒度，包含特写、中景、远景等不同镜头",
            "beat": "节奏点分割 - 按情感/动作转折点切分，适合动态剧情"
        }

        # 构建提示词 — 用户自定义 system_prompt 优先，否则用内置默认
        if not system_prompt or system_prompt.strip() == "":
            system_prompt = """You are a professional storyboard artist and visual director.
Your task is to analyze a story/narrative text and split it into visual scenes for image generation.

For each scene, output a JSON object with:
- "scene_id": scene number (1, 2, 3...)
- "scene_title": brief title (2-5 words)
- "scene_description": what's happening in this scene (1-2 sentences)
- "visual_prompt": detailed image generation prompt in English (include characters, pose, expression, environment, lighting, mood)
- "camera_angle": suggested camera angle (close-up, medium shot, wide shot, etc.)
- "mood": emotional tone (happy, tense, peaceful, etc.)

Output a JSON array of scenes. Example:
[
  {
    "scene_id": 1,
    "scene_title": "Morning Coffee",
    "scene_description": "Character sits at a café table, looking out the window.",
    "visual_prompt": "a young woman with black hair sitting at a wooden café table, morning sunlight through window, coffee cup, thoughtful expression, warm lighting",
    "camera_angle": "medium shot",
    "mood": "peaceful"
  }
]"""

        user_prompt = f"""Please split the following story into {max_scenes} or fewer visual scenes.

Split mode: {split_mode} - {mode_desc.get(split_mode, "")}

{f"Characters in the story:{chr(10)}{character_info}" if character_info else ""}

{f"Style hint: {style_hint}" if style_hint else ""}

Story text:
---
{story_text}
---

Output ONLY the JSON array, no other text."""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=4096,
                temperature=0.7,
                stream=False
            )
            
            result_text = response.choices[0].message.content
            
            # 尝试提取JSON
            scenes = self._extract_json(result_text)

            # 统一字段名（LLM用自定义prompt时字段名不可控）
            scenes = [self._normalize_scene(s) for s in scenes]
            
            if not scenes:
                # 如果提取失败，返回错误信息
                scenes = [{"scene_id": 1, "scene_title": "Error", 
                          "scene_description": "Failed to parse AI response",
                          "visual_prompt": story_text[:500],
                          "camera_angle": "medium shot", "mood": "neutral"}]
                summary = f"[Error] AI响应解析失败，原文:\n{result_text[:1000]}"
            else:
                # 生成摘要
                summary_lines = [f"=== 剧情分镜 ({len(scenes)} 个场景) ===\n"]
                for scene in scenes:
                    summary_lines.append(f"场景 {scene.get('scene_id', '?')}: {scene.get('scene_title', '?')}")
                    summary_lines.append(f"  描述: {scene.get('scene_description', '?')}")
                    summary_lines.append(f"  镜头: {scene.get('camera_angle', '?')} | 情绪: {scene.get('mood', '?')}")
                    summary_lines.append(f"  Prompt: {scene.get('visual_prompt', '?')[:80]}...")
                    summary_lines.append("")
                summary = "\n".join(summary_lines)

        except Exception as e:
            scenes = [{"scene_id": 1, "scene_title": "Error",
                      "scene_description": str(e),
                      "visual_prompt": story_text[:500],
                      "camera_angle": "medium shot", "mood": "neutral"}]
            summary = f"[API Error] {str(e)}"

        return (scenes, summary)

    def _extract_json(self, text: str) -> List[Dict]:
        """从AI响应中提取JSON数组，兼容多种格式"""
        import re

        def _normalize(obj):
            """把各种JSON结构统一成 [{}, {}, ...] 格式"""
            if isinstance(obj, list):
                dicts = [item for item in obj if isinstance(item, dict)]
                if dicts:
                    return dicts
                # LLM返回了纯字符串数组（没按格式），包装成标准scene结构
                strings = [item for item in obj if isinstance(item, str)]
                if strings:
                    return [
                        {
                            "scene_id": i + 1,
                            "scene_title": f"Scene {i + 1}",
                            "scene_description": s[:100],
                            "visual_prompt": s,
                            "camera_angle": "medium shot",
                            "mood": "neutral"
                        }
                        for i, s in enumerate(strings)
                    ]
            if isinstance(obj, dict):
                # 常见包装：{"scenes": [...]}, {"data": [...]}, {"result": [...]}
                for v in obj.values():
                    if isinstance(v, list):
                        return _normalize(v)
            return []

        # 1. 直接解析整个文本
        try:
            result = json.loads(text.strip())
            normalized = _normalize(result)
            if normalized:
                return normalized
        except:
            pass

        # 2. 找 ```json ... ``` 块
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                normalized = _normalize(result)
                if normalized:
                    return normalized
            except:
                pass

        # 3. 找 [ ... ] 块
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group(0))
                normalized = _normalize(result)
                if normalized:
                    return normalized
            except:
                pass

        return []

    # LLM用不同prompt时字段名五花八门，统一映射到标准字段
    _KEY_MAP = {
        # scene_id
        "scene_id": "scene_id", "id": "scene_id", "number": "scene_id",
        "scene_number": "scene_id", "no": "scene_id", "index": "scene_id",
        # scene_title
        "scene_title": "scene_title", "title": "scene_title", "name": "scene_title",
        "heading": "scene_title",
        # scene_description
        "scene_description": "scene_description", "description": "scene_description",
        "desc": "scene_description", "summary": "scene_description",
        "scene_desc": "scene_description", "narrative": "scene_description",
        # visual_prompt
        "visual_prompt": "visual_prompt", "prompt": "visual_prompt",
        "image_prompt": "visual_prompt", "img_prompt": "visual_prompt",
        "sd_prompt": "visual_prompt", "generation_prompt": "visual_prompt",
        # camera_angle
        "camera_angle": "camera_angle", "camera": "camera_angle", "shot": "camera_angle",
        "angle": "camera_angle", "shot_type": "camera_angle", "framing": "camera_angle",
        # mood
        "mood": "mood", "emotion": "mood", "tone": "mood",
        "atmosphere": "mood", "feeling": "mood",
    }

    def _normalize_scene(self, scene: dict) -> dict:
        """把LLM返回的各种字段名统一成标准格式"""
        result = {}
        for k, v in scene.items():
            key = self._KEY_MAP.get(k.lower().strip(), k.lower().strip())
            result[key] = v

        # 补齐缺失字段
        defaults = {
            "scene_id": "?",
            "scene_title": "?",
            "scene_description": "?",
            "visual_prompt": "",
            "camera_angle": "medium shot",
            "mood": "neutral",
        }
        for field, fallback in defaults.items():
            if field not in result or not result[field]:
                result[field] = fallback

        return result


# ============================================================
# 2. 场景选择节点 - 从场景列表中选择一个
# ============================================================
class Pandai_Scene_Selector:
    """
    场景选择节点
    从场景列表中选择指定序号的场景，用于逐个生成图片
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_list": ("SCENE_LIST",),
                "scene_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "选择第几个场景（从0开始）"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "INT")
    RETURN_NAMES = ("visual_prompt", "scene_title", "scene_description", "mood", "total_scenes")
    FUNCTION = "select_scene"
    CATEGORY = "Pandai/Story"

    def select_scene(self, scene_list, scene_index=0):
        total = len(scene_list)
        
        if total == 0:
            return ("", "Empty", "No scenes", "neutral", 0)
        
        # 防止越界
        if scene_index >= total:
            scene_index = total - 1
        
        scene = scene_list[scene_index]
        
        visual_prompt = scene.get("visual_prompt", "")
        scene_title = scene.get("scene_title", f"Scene {scene_index + 1}")
        scene_description = scene.get("scene_description", "")
        mood = scene.get("mood", "neutral")
        
        return (visual_prompt, scene_title, scene_description, mood, total)


# ============================================================
# 3. 场景列表查看节点
# ============================================================
class Pandai_Scene_List_View:
    """
    查看场景列表的详细内容
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_list": ("SCENE_LIST",),
            },
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("scenes_text", "total_scenes")
    FUNCTION = "view_scenes"
    CATEGORY = "Pandai/Story"

    def view_scenes(self, scene_list):
        total = len(scene_list)
        
        lines = [f"=== 场景列表 ({total} 个场景) ===\n"]
        
        for scene in scene_list:
            sid = scene.get("scene_id", "?")
            title = scene.get("scene_title", "?")
            desc = scene.get("scene_description", "")
            prompt = scene.get("visual_prompt", "")
            angle = scene.get("camera_angle", "?")
            mood = scene.get("mood", "?")
            
            lines.append(f"[场景 {sid}] {title}")
            lines.append(f"  描述: {desc}")
            lines.append(f"  镜头: {angle} | 情绪: {mood}")
            lines.append(f"  Prompt: {prompt}")
            lines.append("")
        
        return ("\n".join(lines), total)


# ============================================================
# 4. 批量Prompt输出节点 - 一次性输出所有prompt
# ============================================================
class Pandai_Scene_Batch_Output:
    """
    批量输出所有场景的prompt
    用分隔符隔开，方便复制到其他工具批量生成
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "scene_list": ("SCENE_LIST",),
                "separator": ("STRING", {
                    "default": "---",
                    "multiline": False,
                    "tooltip": "场景之间的分隔符"
                }),
                "include_metadata": (["yes", "no"], {
                    "default": "yes",
                    "tooltip": "是否包含场景标题等元信息"
                }),
            },
            "optional": {
                "character_list": ("CHARACTER_LIST",),
                "prepend_character": (["yes", "no"], {
                    "default": "yes",
                    "tooltip": "是否在每个prompt前面加上角色描述"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("all_prompts", "prompts_only")
    FUNCTION = "batch_output"
    CATEGORY = "Pandai/Story"

    def batch_output(self, scene_list, separator="---", include_metadata="yes",
                     character_list=None, prepend_character="yes"):
        
        # 构建角色前缀
        char_prefix = ""
        if character_list and prepend_character == "yes":
            char_parts = []
            for char in character_list:
                desc = f"{char['name']}: {char['age']} {char['gender']}"
                if char['appearance']:
                    desc += f", {char['appearance']}"
                if char['clothing']:
                    desc += f", wearing {char['clothing']}"
                if char['features']:
                    desc += f", {char['features']}"
                char_parts.append(desc)
            char_prefix = "Characters: " + "; ".join(char_parts) + "\n\n"

        all_prompts_lines = []
        prompts_only_lines = []
        
        for i, scene in enumerate(scene_list):
            sid = scene.get("scene_id", i + 1)
            title = scene.get("scene_title", f"Scene {sid}")
            desc = scene.get("scene_description", "")
            prompt = scene.get("visual_prompt", "")
            angle = scene.get("camera_angle", "")
            mood = scene.get("mood", "")
            
            # 完整输出
            if include_metadata == "yes":
                all_prompts_lines.append(f"[Scene {sid}] {title}")
                all_prompts_lines.append(f"Description: {desc}")
                all_prompts_lines.append(f"Camera: {angle} | Mood: {mood}")
                all_prompts_lines.append(f"Prompt: {char_prefix}{prompt}")
            else:
                all_prompts_lines.append(f"{char_prefix}{prompt}")
            
            # 纯prompt输出
            prompts_only_lines.append(f"{char_prefix}{prompt}")
            
            if i < len(scene_list) - 1:
                all_prompts_lines.append(separator)
                prompts_only_lines.append(separator)
        
        return ("\n".join(all_prompts_lines), "\n".join(prompts_only_lines))


# ============================================================
# Register
# ============================================================
NODE_CLASS_MAPPINGS = {
    "Pandai_Story_Splitter": Pandai_Story_Splitter,
    "Pandai_Scene_Selector": Pandai_Scene_Selector,
    "Pandai_Scene_List_View": Pandai_Scene_List_View,
    "Pandai_Scene_Batch_Output": Pandai_Scene_Batch_Output,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Pandai_Story_Splitter": "Pandai 剧情分镜",
    "Pandai_Scene_Selector": "Pandai 场景选择",
    "Pandai_Scene_List_View": "Pandai 场景列表查看",
    "Pandai_Scene_Batch_Output": "Pandai 批量Prompt输出",
}
