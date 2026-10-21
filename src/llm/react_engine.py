"""ReAct 循环引擎：基于 ChatOllama 的 bind_tools。

- react_loop：工具调用循环（思考-行动-观察），支持轮次上限与退出原因。
- run_structured：用 with_structured_output 直接产出结构化对象。
"""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from src.llm.client import get_llm


def react_loop(
    system_prompt: str,
    user_prompt: str,
    tools: dict[str, object] | None = None,
    max_rounds: int = 6,
) -> tuple[dict, str]:
    """执行 ReAct 工具调用循环。

    Args:
        system_prompt: 系统提示词
        user_prompt: 用户任务
        tools: 工具集 {名称: LangChain Tool 对象}
        max_rounds: 最大推理轮次

    Returns:
        ({"content": 最终文本}, 退出原因)
        退出原因：llm_finish / max_rounds
    """
    tools = tools or {}
    llm = get_llm()
    if tools:
        llm = llm.bind_tools(list(tools.values()))

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]

    for _ in range(1, max_rounds + 1):
        resp = llm.invoke(messages)

        # 有工具调用则执行并观察
        if resp.tool_calls:
            messages.append(resp)
            for tc in resp.tool_calls:
                name = tc["name"]
                if name in tools:
                    result = tools[name].invoke(tc["args"])
                    messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
            continue

        # 无工具调用，视为最终结果
        return {"content": resp.content}, "llm_finish"

    return {}, "max_rounds"


def run_structured(system_prompt: str, user_prompt: str, output_schema):
    """用 with_structured_output 直接产出结构化对象。"""
    llm = get_llm().with_structured_output(output_schema)
    return llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
