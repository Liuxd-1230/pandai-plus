# Main nodes
from .pandai_nodes import NODE_CLASS_MAPPINGS as MAIN_NODES

# Story/分镜 nodes
from .pandai_story_nodes import NODE_CLASS_MAPPINGS as STORY_NODES

# Image nodes
from .pandai_image_nodes import NODE_CLASS_MAPPINGS as IMAGE_NODES

# Merge all node mappings
NODE_CLASS_MAPPINGS = {**MAIN_NODES, **STORY_NODES, **IMAGE_NODES}

NODE_DISPLAY_NAME_MAPPINGS = {
    # Config & LLM nodes
    "Pandai_API_Config": "Pandai API 配置",
    "Pandai_API_Test": "Pandai API 测试",
    "Pandai_Character_Anchor": "Pandai 人物外貌锚点",
    "Pandai_Character_Merge": "Pandai 人物合并",
    "Pandai_DSK_Chat": "Pandai LLM 对话",
    "Pandai_History_Clear": "Pandai 历史清空",
    "Pandai_History_View": "Pandai 历史查看",
    "Pandai_Prompt_File_Loader": "Pandai Prompt 文件加载",
    
    # Story/分镜 nodes
    "Pandai_Story_Splitter": "Pandai 剧情分镜",
    "Pandai_Scene_Selector": "Pandai 场景选择",
    "Pandai_Scene_List_View": "Pandai 场景列表查看",
    "Pandai_Scene_Batch_Output": "Pandai 批量Prompt输出",
    
    # Image nodes
    "Pandai_Image_Analyzer": "Pandai 图片分析",
    "Pandai_Img2Img_Prompt": "Pandai 图生图Prompt",
    "Pandai_Style_Transfer_Prompt": "Pandai 风格迁移Prompt",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
