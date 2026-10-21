"""ReAct 上下文处理器。"""
from __future__ import annotations


class ReActContext:
    """管理 ReAct 循环的消息历史，支持 token 估算与上下文压缩。"""

    def __init__(self, max_tokens: int = 4000):
        self.messages: list[dict] = []
        self.max_tokens = max_tokens

    def add_message(self, role: str, content: str) -> None:
        """添加消息到上下文。"""
        self.messages.append({"role": role, "content": content})

    def get_messages(self) -> list[dict]:
        """获取当前上下文消息。"""
        return self.messages

    def _should_compress(self) -> bool:
        """判断是否需要压缩上下文。"""
        return self._estimate_tokens() > self.max_tokens

    def _estimate_tokens(self) -> int:
        """估算当前上下文的总 token 数。"""
        return sum(self._estimate_text_tokens(m.get("content", "")) for m in self.messages)

    @staticmethod
    def _estimate_text_tokens(text: str) -> int:
        """估算文本 token 数（中文约 1.5 字/token）。"""
        return int(len(text) / 1.5)

    def _compress_messages(self) -> None:
        """压缩上下文：保留 system + 最近的完整轮次。"""
        system = [m for m in self.messages if m["role"] == "system"]
        recent = self.messages[-4:]
        self.messages = system + recent

    def _generate_summary(self, messages: list[dict]) -> str:
        """生成历史消息摘要（可调用 LLM 或规则提取）。"""
        return "…（历史消息已压缩）…"
