"""结构化输出解析器。"""
import json
import re


def parse_output(text: str) -> dict:
    """从 LLM 文本中提取 JSON 对象，失败抛出 ValueError。

    支持三种情况：
    1. 纯 JSON 文本
    2. ```json ... ``` 代码块
    3. 文本中夹带的 {...} 块
    """
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ValueError(f"无法解析 JSON 输出: {text[:120]}")


def parse_tool_call(text: str) -> tuple[str, dict] | None:
    """从 LLM 文本中解析工具调用，格式 {"tool": "xxx", "args": {...}}。"""
    try:
        obj = parse_output(text)
    except ValueError:
        return None
    if isinstance(obj, dict) and "tool" in obj:
        return obj["tool"], obj.get("args", {})
    return None
