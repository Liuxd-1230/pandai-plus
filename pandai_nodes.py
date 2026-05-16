import json
import requests
from typing import List, Dict, Optional, Tuple


# ============================================================
# 1. API配置节点
# ============================================================
class Pandai_API_Config:
    """API Configuration node - stores API URL and API Key."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_url": ("STRING", {
                    "multiline": False,
                    "default": "https://api.deepseek.com",
                    "placeholder": "https://api.deepseek.com"
                }),
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "sk-..."
                }),
            },
            "optional": {
                "default_model": ("STRING", {
                    "multiline": False,
                    "default": "deepseek-chat",
                    "placeholder": "deepseek-chat"
                }),
            }
        }

    RETURN_TYPES = ("API_CONFIG",)
    RETURN_NAMES = ("api_config",)
    FUNCTION = "configure"
    CATEGORY = "Pandai/Config"

    def configure(self, api_url, api_key, default_model="deepseek-chat"):
        # 确保URL不以/结尾
        api_url = api_url.rstrip("/")
        config = {
            "api_url": api_url,
            "api_key": api_key,
            "default_model": default_model
        }
        return (config,)


# ============================================================
# 2. API测试节点
# ============================================================
class Pandai_API_Test:
    """Test API connectivity and fetch available models."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_config": ("API_CONFIG",),
                "test_mode": (["connectivity", "list_models", "both"], {
                    "default": "both"
                }),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("test_result", "models_list")
    FUNCTION = "test_api"
    CATEGORY = "Pandai/Config"

    def test_api(self, api_config, test_mode="both"):
        api_url = api_config["api_url"]
        api_key = api_config["api_key"]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        result_lines = []
        models_list = ""

        # Test connectivity
        if test_mode in ["connectivity", "both"]:
            try:
                # 尝试调用一个简单的API端点
                test_url = f"{api_url}/v1/models"
                resp = requests.get(test_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    result_lines.append("[OK] API连接成功!")
                    result_lines.append(f"状态码: {resp.status_code}")
                else:
                    result_lines.append(f"[FAIL] API返回状态码: {resp.status_code}")
                    try:
                        err = resp.json()
                        result_lines.append(f"错误信息: {json.dumps(err, ensure_ascii=False)}")
                    except:
                        result_lines.append(f"响应内容: {resp.text[:500]}")
            except requests.exceptions.ConnectionError as e:
                result_lines.append(f"[FAIL] 连接失败: 无法连接到 {api_url}")
                result_lines.append(f"请检查URL是否正确以及网络是否可用")
            except requests.exceptions.Timeout:
                result_lines.append(f"[FAIL] 连接超时: {api_url} 响应超时")
            except Exception as e:
                result_lines.append(f"[FAIL] 测试失败: {str(e)}")

        # List models
        if test_mode in ["list_models", "both"]:
            try:
                models_url = f"{api_url}/v1/models"
                resp = requests.get(models_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    if "data" in data:
                        model_ids = [m.get("id", "unknown") for m in data["data"]]
                        models_list = "\n".join(model_ids)
                        result_lines.append(f"\n[OK] 获取到 {len(model_ids)} 个模型:")
                        for mid in model_ids:
                            result_lines.append(f"  - {mid}")
                    else:
                        result_lines.append("[WARN] 响应中没有data字段")
                        result_lines.append(f"响应: {json.dumps(data, ensure_ascii=False)[:500]}")
                else:
                    result_lines.append(f"[FAIL] 获取模型列表失败: {resp.status_code}")
            except Exception as e:
                result_lines.append(f"[FAIL] 获取模型列表失败: {str(e)}")

        if not models_list:
            models_list = "(无法获取模型列表)"

        return ("\n".join(result_lines), models_list)


# ============================================================
# 3. 人物外貌锚点节点
# ============================================================
class Pandai_Character_Anchor:
    """
    Character appearance anchor node.
    Define character appearance descriptions that will be consistently
    applied across multiple image generation prompts.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_name": ("STRING", {
                    "multiline": False,
                    "default": "主角",
                    "placeholder": "角色名称，如：小红、Alice"
                }),
                "gender": (["female", "male", "other"],),
                "age_range": (["child", "teen", "young_adult", "adult", "middle_aged", "elderly"], {
                    "default": "young_adult"
                }),
                "appearance_description": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "详细外貌描述，如：黑色长发，大眼睛，瓜子脸，皮肤白皙，身材纤细"
                }),
            },
            "optional": {
                "clothing_style": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "服装风格描述（可选）"
                }),
                "distinctive_features": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "标志性特征，如：左脸有酒窝、戴红色发卡"
                }),
                "existing_characters": ("CHARACTER_LIST",),
            }
        }

    RETURN_TYPES = ("CHARACTER_LIST", "STRING")
    RETURN_NAMES = ("character_list", "character_prompt")
    FUNCTION = "add_character"
    CATEGORY = "Pandai/Character"

    # 年龄范围翻译
    AGE_MAP = {
        "child": "child (6-12 years old)",
        "teen": "teenager (13-17 years old)",
        "young_adult": "young adult (18-25 years old)",
        "adult": "adult (26-40 years old)",
        "middle_aged": "middle-aged (41-60 years old)",
        "elderly": "elderly (60+ years old)"
    }

    GENDER_MAP = {
        "female": "female",
        "male": "male",
        "other": "androgynous"
    }

    def add_character(self, character_name, gender, age_range, appearance_description,
                      clothing_style="", distinctive_features="", existing_characters=None):

        # 创建角色字典
        character = {
            "name": character_name,
            "gender": self.GENDER_MAP.get(gender, gender),
            "age": self.AGE_MAP.get(age_range, age_range),
            "appearance": appearance_description,
            "clothing": clothing_style,
            "features": distinctive_features
        }

        # 合并已有角色列表
        characters = []
        if existing_characters is not None:
            characters = existing_characters.copy()
        characters.append(character)

        # 生成角色提示词
        character_prompt = self._build_character_prompt(characters)

        return (characters, character_prompt)

    def _build_character_prompt(self, characters: List[Dict]) -> str:
        """Build a combined prompt for all characters."""
        if not characters:
            return ""

        parts = []
        for i, char in enumerate(characters, 1):
            char_parts = []
            if char["name"]:
                char_parts.append(f"Character '{char['name']}'")
            char_parts.append(f"{char['age']} {char['gender']}")
            if char["appearance"]:
                char_parts.append(char["appearance"])
            if char["clothing"]:
                char_parts.append(f"wearing {char['clothing']}")
            if char["features"]:
                char_parts.append(char["features"])

            parts.append(", ".join(char_parts))

        return "Characters: " + "; ".join(parts)


# ============================================================
# 4. 人物列表合并节点（用于多人物场景）
# ============================================================
class Pandai_Character_Merge:
    """Merge multiple character lists into one."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "character_list_1": ("CHARACTER_LIST",),
                "character_list_2": ("CHARACTER_LIST",),
            },
            "optional": {
                "character_list_3": ("CHARACTER_LIST",),
                "character_list_4": ("CHARACTER_LIST",),
            }
        }

    RETURN_TYPES = ("CHARACTER_LIST", "STRING")
    RETURN_NAMES = ("merged_characters", "merged_prompt")
    FUNCTION = "merge_characters"
    CATEGORY = "Pandai/Character"

    def merge_characters(self, character_list_1, character_list_2,
                         character_list_3=None, character_list_4=None):
        merged = character_list_1.copy() + character_list_2.copy()
        if character_list_3:
            merged += character_list_3.copy()
        if character_list_4:
            merged += character_list_4.copy()

        # 生成合并后的提示词
        prompt_parts = []
        for char in merged:
            char_desc = f"{char['name']}: {char['age']} {char['gender']}"
            if char['appearance']:
                char_desc += f", {char['appearance']}"
            if char['clothing']:
                char_desc += f", wearing {char['clothing']}"
            if char['features']:
                char_desc += f", {char['features']}"
            prompt_parts.append(char_desc)

        prompt = "Characters in scene: " + "; ".join(prompt_parts)
        return (merged, prompt)


# ============================================================
# 5. 改进的LLM对话节点
# ============================================================
class Pandai_DSK_Chat:
    """
    Improved LLM chat node with:
    - Configurable API URL and Key
    - Character anchor support
    - Better history management (sliding window)
    - Streaming support option
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_config": ("API_CONFIG",),
                "model": ("STRING", {
                    "multiline": False,
                    "default": "deepseek-chat",
                    "placeholder": "model name"
                }),
                "system_prompt": ("STRING", {
                    "default": "You are a helpful assistant.",
                    "multiline": True
                }),
                "user_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入你的问题或指令"
                }),
                "max_tokens": ("INT", {
                    "default": 4096,
                    "min": 1,
                    "max": 32768,
                    "step": 1
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0,
                    "max": 2,
                    "step": 0.05
                }),
            },
            "optional": {
                "character_list": ("CHARACTER_LIST",),
                "character_prompt_mode": (["prepend_to_system", "prepend_to_user", "append_to_user"], {
                    "default": "prepend_to_user"
                }),
                "chat_history": ("CHAT_HISTORY",),
                "history_mode": (["sliding_window", "full", "none"], {
                    "default": "sliding_window"
                }),
                "max_history_turns": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
                "top_p": ("FLOAT", {"default": 1.0, "min": 0, "max": 1, "step": 0.05}),
                "presence_penalty": ("FLOAT", {"default": 0, "min": -2, "max": 2, "step": 0.1}),
                "frequency_penalty": ("FLOAT", {"default": 0, "min": -2, "max": 2, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("STRING", "CHAT_HISTORY")
    RETURN_NAMES = ("response", "chat_history")
    FUNCTION = "chat"
    CATEGORY = "Pandai/LLM"

    def chat(self, api_config, model, system_prompt, user_prompt,
             max_tokens, temperature,
             character_list=None, character_prompt_mode="prepend_to_user",
             chat_history=None, history_mode="sliding_window", max_history_turns=10,
             top_p=1.0, presence_penalty=0, frequency_penalty=0):

        from openai import OpenAI

        api_url = api_config["api_url"]
        api_key = api_config["api_key"]

        # 使用配置中的默认模型（如果用户没改）
        if not model or model.strip() == "":
            model = api_config.get("default_model", "deepseek-chat")

        client = OpenAI(api_key=api_key, base_url=f"{api_url}/v1")

        # 构建角色提示词
        character_prompt = ""
        if character_list:
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
            character_prompt = "Scene characters (maintain consistency):\n" + "\n".join(char_parts)

        # 构建消息列表
        messages = []

        # 系统提示词
        final_system_prompt = system_prompt
        if character_prompt and character_prompt_mode == "prepend_to_system":
            final_system_prompt = f"{character_prompt}\n\n{system_prompt}"
        messages.append({"role": "system", "content": final_system_prompt})

        # 处理历史记录
        if chat_history is not None and history_mode != "none":
            history_messages = chat_history.get("messages", [])

            if history_mode == "sliding_window":
                # 滑动窗口：只保留最近N轮对话
                # 每轮 = 1 user + 1 assistant
                max_msgs = max_history_turns * 2
                if len(history_messages) > max_msgs:
                    history_messages = history_messages[-max_msgs:]

            # 添加历史消息（跳过第一条system message如果存在）
            for msg in history_messages:
                if msg["role"] != "system":
                    messages.append(msg)

        # 构建用户提示词
        final_user_prompt = user_prompt
        if character_prompt:
            if character_prompt_mode == "prepend_to_user":
                final_user_prompt = f"{character_prompt}\n\n{user_prompt}"
            elif character_prompt_mode == "append_to_user":
                final_user_prompt = f"{user_prompt}\n\n{character_prompt}"

        messages.append({"role": "user", "content": final_user_prompt})

        # 调用API
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                presence_penalty=presence_penalty,
                frequency_penalty=frequency_penalty,
                stream=False
            )
            response_text = response.choices[0].message.content
        except Exception as e:
            response_text = f"[API Error] {str(e)}"

        # 更新历史记录
        messages.append({"role": "assistant", "content": response_text})

        # 创建新的history对象
        new_history = {"messages": messages}

        return (response_text, new_history)


# ============================================================
# 6. 历史记录清理节点
# ============================================================
class Pandai_History_Clear:
    """Clear chat history and start fresh."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "any_input": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("CHAT_HISTORY",)
    RETURN_NAMES = ("empty_history",)
    FUNCTION = "clear_history"
    CATEGORY = "Pandai/LLM"

    def clear_history(self, any_input):
        return ({"messages": []},)


# ============================================================
# 7. 历史记录查看节点
# ============================================================
class Pandai_History_View:
    """View chat history as formatted text."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "chat_history": ("CHAT_HISTORY",),
            },
            "optional": {
                "max_display": ("INT", {
                    "default": 20,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
            }
        }

    RETURN_TYPES = ("STRING", "INT")
    RETURN_NAMES = ("history_text", "total_messages")
    FUNCTION = "view_history"
    CATEGORY = "Pandai/LLM"

    def view_history(self, chat_history, max_display=20):
        messages = chat_history.get("messages", [])
        total = len(messages)

        lines = [f"=== Chat History ({total} messages) ===\n"]

        display_msgs = messages[-max_display:] if len(messages) > max_display else messages
        if len(messages) > max_display:
            lines.append(f"... ({len(messages) - max_display} earlier messages hidden) ...\n")

        for i, msg in enumerate(display_msgs):
            role = msg["role"]
            content = msg["content"]
            # 截断过长的内容
            if len(content) > 500:
                content = content[:500] + "..."
            lines.append(f"[{role.upper()}]")
            lines.append(content)
            lines.append("")

        return ("\n".join(lines), total)


# ============================================================
# Register all nodes
# ============================================================
NODE_CLASS_MAPPINGS = {
    "Pandai_API_Config": Pandai_API_Config,
    "Pandai_API_Test": Pandai_API_Test,
    "Pandai_Character_Anchor": Pandai_Character_Anchor,
    "Pandai_Character_Merge": Pandai_Character_Merge,
    "Pandai_DSK_Chat": Pandai_DSK_Chat,
    "Pandai_History_Clear": Pandai_History_Clear,
    "Pandai_History_View": Pandai_History_View,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Pandai_API_Config": "Pandai API Config",
    "Pandai_API_Test": "Pandai API Test",
    "Pandai_Character_Anchor": "Pandai Character Anchor",
    "Pandai_Character_Merge": "Pandai Character Merge",
    "Pandai_DSK_Chat": "Pandai LLM Chat",
    "Pandai_History_Clear": "Pandai History Clear",
    "Pandai_History_View": "Pandai History View",
}
