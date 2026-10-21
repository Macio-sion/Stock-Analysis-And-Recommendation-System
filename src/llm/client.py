"""LLM 客户端（langchain-ollama 的 ChatOllama）。

通过 ChatOllama 对象调用本机 Ollama，支持 bind_tools（工具绑定）
与 with_structured_output（结构化输出）。
"""
from langchain_ollama import ChatOllama

from config.settings import settings


def get_llm(temperature: float = 0.0) -> ChatOllama:
    """返回 ChatOllama 实例。"""
    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=temperature,
    )


def chat(messages: list[dict], temperature: float = 0.0) -> str:
    """简单对话，返回 assistant 文本。"""
    resp = get_llm(temperature=temperature).invoke(messages)
    return resp.content
