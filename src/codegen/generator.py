"""代码生成引擎：LLM 生成 Python 算法代码。"""
from __future__ import annotations

from config.prompts.code_generator import CODE_GEN_SYSTEM_PROMPT
from src.codegen.models import GeneratedCode
from src.llm.react_engine import run_structured


def generate_code(description: str) -> dict:
    """根据算法描述生成 Python 代码。

    Returns:
        GeneratedCode 的字典表示（含 code / entry_point / dependencies 等）。
    """
    result = run_structured(
        CODE_GEN_SYSTEM_PROMPT,
        f"请根据以下算法描述生成推荐算法代码：\n{description}",
        GeneratedCode,
    )
    return result.model_dump()
