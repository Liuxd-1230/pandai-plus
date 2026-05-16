# Original nodes
from .pandai_dsk_node import NODE_CLASS_MAPPINGS as DSK_NODES
from .ZH_DocxTextSplitter import NODE_CLASS_MAPPINGS as DOCX_NODES

# New improved nodes
from .pandai_nodes import NODE_CLASS_MAPPINGS as NEW_NODES

# Merge all node mappings
NODE_CLASS_MAPPINGS = {**DSK_NODES, **DOCX_NODES, **NEW_NODES}

NODE_DISPLAY_NAME_MAPPINGS = {
    # Original nodes (keep for backward compatibility)
    "pandai_dsk_node": "Pandai DSK Node (Legacy)",
    "ZH_DocxTextSplitter": "ZH-Docx文本分割器",
    
    # New nodes
    "Pandai_API_Config": "Pandai API 配置",
    "Pandai_API_Test": "Pandai API 测试",
    "Pandai_Character_Anchor": "Pandai 人物外貌锚点",
    "Pandai_Character_Merge": "Pandai 人物合并",
    "Pandai_DSK_Chat": "Pandai LLM 对话",
    "Pandai_History_Clear": "Pandai 历史记录清空",
    "Pandai_History_View": "Pandai 历史记录查看",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
