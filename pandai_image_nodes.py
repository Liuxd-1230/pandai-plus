import json
import base64
import requests
from typing import Dict, List, Optional, Tuple


# ============================================================
# 1. 图片分析节点 - 用视觉LLM分析图片内容
# ============================================================
class Pandai_Image_Analyzer:
    """
    图片分析节点
    使用视觉LLM（GPT-4V、Claude 3、本地LLaVA等）分析图片内容
    输出图片描述，可用于生成相似风格的图片
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_config": ("API_CONFIG",),
                "model": ("STRING", {
                    "multiline": False,
                    "default": "deepseek-chat",
                    "placeholder": "视觉模型名称"
                }),
                "image": ("IMAGE",),
                "analysis_mode": (["describe", "prompt", "style", "character"], {
                    "default": "describe",
                    "tooltip": "describe=通用描述，prompt=生成图片prompt，style=提取风格，character=提取人物外貌"
                }),
            },
            "optional": {
                "custom_question": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "自定义问题（可选），如：这张图的光线是怎么处理的？"
                }),
                "language": (["english", "chinese"], {
                    "default": "english",
                    "tooltip": "输出语言"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("analysis", "extracted_prompt")
    FUNCTION = "analyze_image"
    CATEGORY = "Pandai/Image"

    def analyze_image(self, api_config, model, image, analysis_mode="describe",
                      custom_question="", language="english"):

        from openai import OpenAI

        api_url = api_config["api_url"]
        api_key = api_config["api_key"]

        if not model or model.strip() == "":
            model = api_config.get("default_model", "deepseek-chat")

        base_url = api_url if api_url.endswith("/v1") else f"{api_url}/v1"

        # 将ComfyUI的IMAGE tensor转换为base64
        import torch
        import numpy as np
        from PIL import Image
        import io

        # ComfyUI的IMAGE格式是 [batch, height, width, channels]，值范围0-1
        if isinstance(image, torch.Tensor):
            img_tensor = image[0]  # 取第一张
            img_np = (img_tensor.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
        else:
            pil_image = Image.fromarray((image[0] * 255).astype(np.uint8))

        # 转为base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        # 根据分析模式构建提示词
        mode_prompts = {
            "describe": {
                "english": "Describe this image in detail. Include the subject, composition, colors, lighting, mood, and any notable elements.",
                "chinese": "详细描述这张图片。包括主体、构图、色彩、光线、情绪和任何值得注意的元素。"
            },
            "prompt": {
                "english": "Analyze this image and generate a detailed Stable Diffusion prompt that could recreate a similar image. Include subject description, art style, lighting, colors, composition, and quality tags. Output ONLY the prompt, no explanations.",
                "chinese": "分析这张图片，生成一个详细的Stable Diffusion提示词，用于创建类似图片。包括主体描述、艺术风格、光线、色彩、构图和质量标签。只输出提示词，不要解释。"
            },
            "style": {
                "english": "Analyze the artistic style of this image. Describe the art style, color palette, brushwork/technique, lighting style, and overall aesthetic. Be specific about what makes this style unique.",
                "chinese": "分析这张图片的艺术风格。描述画风、色彩搭配、笔触/技法、光线风格和整体美学。具体说明这种风格的独特之处。"
            },
            "character": {
                "english": "Focus on the character(s) in this image. Describe their appearance in detail: hair color/style, eye color, facial features, skin tone, body type, clothing, accessories, pose, and expression. Be very specific for character consistency.",
                "chinese": "专注于图片中的角色。详细描述外貌：发色/发型、眼睛颜色、面部特征、肤色、体型、服装、配饰、姿势和表情。请非常具体以保持角色一致性。"
            }
        }

        system_prompt = "You are an expert image analyst and AI art prompt engineer."
        
        if custom_question:
            user_prompt = custom_question
        else:
            user_prompt = mode_prompts.get(analysis_mode, mode_prompts["describe"]).get(language, mode_prompts["describe"]["english"])

        # 调用视觉API
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)

            # 检查模型是否支持视觉
            # 大多数视觉模型使用这个格式
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ]

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=2048,
                temperature=0.7,
                stream=False
            )

            analysis = response.choices[0].message.content

            # 如果是prompt模式，提取的prompt就是分析结果
            if analysis_mode == "prompt":
                extracted_prompt = analysis
            else:
                # 否则，尝试从分析中提取可用的prompt片段
                extracted_prompt = self._extract_prompt_elements(analysis, analysis_mode)

        except Exception as e:
            analysis = f"[Error] {str(e)}"
            extracted_prompt = ""

        return (analysis, extracted_prompt)

    def _extract_prompt_elements(self, analysis: str, mode: str) -> str:
        """从分析结果中提取可用于prompt的元素"""
        # 简单提取：取前500个字符作为prompt基础
        if len(analysis) > 500:
            return analysis[:500] + "..."
        return analysis


# ============================================================
# 2. 图生图Prompt生成节点
# ============================================================
class Pandai_Img2Img_Prompt:
    """
    图生图Prompt生成节点
    基于参考图片分析和角色锚点，生成适合图生图的prompt
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
                "reference_analysis": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "参考图片的分析结果（从图片分析节点获取）"
                }),
                "user_request": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "你想要的效果，如：保持风格不变，但把人物换成小红"
                }),
            },
            "optional": {
                "character_list": ("CHARACTER_LIST",),
                "preserve_elements": (["style", "composition", "lighting", "all", "none"], {
                    "default": "style",
                    "tooltip": "从参考图保留哪些元素"
                }),
                "strength": ("FLOAT", {
                    "default": 0.7,
                    "min": 0,
                    "max": 1,
                    "step": 0.05,
                    "tooltip": "变换强度建议（0.3=微调，0.5=中等，0.7=较大变化）"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "FLOAT")
    RETURN_NAMES = ("img2img_prompt", "negative_prompt", "suggested_strength")
    FUNCTION = "generate_prompt"
    CATEGORY = "Pandai/Image"

    def generate_prompt(self, api_config, model, reference_analysis, user_request,
                        character_list=None, preserve_elements="style", strength=0.7):

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
            character_info = "Characters to include:\n" + "\n".join(char_parts)

        # 保留元素说明
        preserve_desc = {
            "style": "art style, color palette, overall aesthetic",
            "composition": "composition, framing, camera angle",
            "lighting": "lighting, shadows, atmosphere",
            "all": "style, composition, lighting, and overall mood",
            "none": "only the core concept, everything else can change"
        }

        system_prompt = """You are an expert Stable Diffusion prompt engineer specializing in img2img.

Your task is to generate a prompt for img2img generation based on:
1. A reference image analysis
2. User's request for changes
3. Character descriptions (if provided)

Output TWO things separated by [NEGATIVE]:
1. The positive prompt (what you want)
2. The negative prompt (what to avoid)

Example format:
beautiful woman in red dress standing in garden, masterpiece, best quality, highly detailed
[NEGATIVE]
blurry, low quality, deformed, ugly, bad anatomy, extra limbs"""

        user_prompt = f"""Reference image analysis:
{reference_analysis}

User request: {user_request}

{character_info if character_info else ""}

Preserve from reference: {preserve_desc.get(preserve_elements, "style")}

Generate img2img prompt that combines the reference image's {preserve_elements} with the user's request.
If character descriptions are provided, incorporate them into the prompt for character consistency.

Output format:
[positive prompt]
[NEGATIVE]
[negative prompt]"""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=2048,
                temperature=0.7,
                stream=False
            )

            result = response.choices[0].message.content

            # 解析输出
            if "[NEGATIVE]" in result:
                parts = result.split("[NEGATIVE]")
                img2img_prompt = parts[0].strip()
                negative_prompt = parts[1].strip()
            else:
                img2img_prompt = result.strip()
                negative_prompt = "blurry, low quality, deformed, ugly, bad anatomy, extra limbs, watermark, text"

        except Exception as e:
            img2img_prompt = f"[Error] {str(e)}"
            negative_prompt = ""

        return (img2img_prompt, negative_prompt, strength)


# ============================================================
# 3. 图片混合/风格迁移提示节点
# ============================================================
class Pandai_Style_Transfer_Prompt:
    """
    风格迁移Prompt生成
    将一张图的风格应用到另一张图的内容上
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "api_config": ("API_CONFIG",),
                "model": ("STRING", {"multiline": False, "default": "deepseek-chat"}),
                "content_description": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "内容图的描述（或从图片分析节点获取）"
                }),
                "style_description": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "风格图的描述（或从图片分析节点获取）"
                }),
            },
            "optional": {
                "character_list": ("CHARACTER_LIST",),
                "style_weight": ("FLOAT", {
                    "default": 0.6,
                    "min": 0,
                    "max": 1,
                    "step": 0.05,
                    "tooltip": "风格权重（0=只用内容，1=只用风格）"
                }),
                "system_prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "自定义系统提示词（留空使用内置默认）。用于控制LLM如何融合风格和内容，例如：指定画风标签、质量要求、输出格式等"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("transfer_prompt", "negative_prompt")
    FUNCTION = "generate_transfer_prompt"
    CATEGORY = "Pandai/Image"

    def generate_transfer_prompt(self, api_config, model, content_description, style_description,
                                  character_list=None, style_weight=0.6, system_prompt=""):

        from openai import OpenAI

        api_url = api_config["api_url"]
        api_key = api_config["api_key"]

        if not model or model.strip() == "":
            model = api_config.get("default_model", "deepseek-chat")

        base_url = api_url if api_url.endswith("/v1") else f"{api_url}/v1"
        client = OpenAI(api_key=api_key, base_url=base_url)

        character_info = ""
        if character_list:
            char_parts = []
            for char in character_list:
                desc = f"{char['name']}: {char['appearance']}"
                char_parts.append(desc)
            character_info = "Characters: " + "; ".join(char_parts)

        if not system_prompt or system_prompt.strip() == "":
            system_prompt = """You are an expert at combining artistic styles with image content.
Generate a Stable Diffusion prompt that applies the style from one image to the content of another.

Output format:
[positive prompt]
[NEGATIVE]
[negative prompt]"""

        user_prompt = f"""Content to render: {content_description}

Style to apply: {style_description}

Style weight: {style_weight} (0=content only, 1=style only)

{character_info if character_info else ""}

Generate a prompt that renders the content in the given style.
Output format:
[positive prompt]
[NEGATIVE]
[negative prompt]"""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1500,
                temperature=0.7,
                stream=False
            )

            result = response.choices[0].message.content

            if "[NEGATIVE]" in result:
                parts = result.split("[NEGATIVE]")
                transfer_prompt = parts[0].strip()
                negative_prompt = parts[1].strip()
            else:
                transfer_prompt = result.strip()
                negative_prompt = "blurry, low quality, deformed, ugly, bad anatomy"

        except Exception as e:
            transfer_prompt = f"[Error] {str(e)}"
            negative_prompt = ""

        return (transfer_prompt, negative_prompt)


# ============================================================
# Register
# ============================================================
NODE_CLASS_MAPPINGS = {
    "Pandai_Image_Analyzer": Pandai_Image_Analyzer,
    "Pandai_Img2Img_Prompt": Pandai_Img2Img_Prompt,
    "Pandai_Style_Transfer_Prompt": Pandai_Style_Transfer_Prompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Pandai_Image_Analyzer": "Pandai 图片分析",
    "Pandai_Img2Img_Prompt": "Pandai 图生图Prompt",
    "Pandai_Style_Transfer_Prompt": "Pandai 风格迁移Prompt",
}
