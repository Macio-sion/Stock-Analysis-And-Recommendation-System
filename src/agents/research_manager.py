"""研究经理（ReAct）：多空裁决 → ComprehensiveReport。"""
from __future__ import annotations

import json

from langchain_core.tools import tool

from config.prompts.research_manager import MANAGER_SYSTEM_PROMPT
from src.agents.researcher_models import ComprehensiveReport
from src.llm.react_engine import react_loop, run_structured


def _rating_from_score(score: int) -> str:
    """根据综合评分映射评级。"""
    if score >= 80:
        return "强烈看多"
    if score >= 60:
        return "看多"
    if score >= 40:
        return "中性"
    if score >= 20:
        return "看空"
    return "强烈看空"


def run_manager(state: dict) -> dict:
    """研究经理节点。

    Args:
        state: 含 bull_report / bear_report / symbol / 三维度得分

    Returns:
        {"comprehensive_report": dict, "exit_reason": str}
    """
    bull = state["bull_report"]
    bear = state["bear_report"]
    symbol = state.get("symbol") or state.get("ts_code", "")

    @tool
    def read_bull_report() -> str:
        """读取多头研究员的观点报告。"""
        return json.dumps(bull, ensure_ascii=False)

    @tool
    def read_bear_report() -> str:
        """读取空头研究员的观点报告。"""
        return json.dumps(bear, ensure_ascii=False)

    @tool
    def search_report(keyword: str) -> str:
        """在多空报告中按关键词搜索相关内容。"""
        results = []
        for name, report in [("bull", bull), ("bear", bear)]:
            text = json.dumps(report, ensure_ascii=False)
            if keyword in text:
                results.append(f"[{name}] {text[:500]}")
        return "\n---\n".join(results) if results else f"未找到与 '{keyword}' 相关的内容"

    tools = {
        "read_bull_report": read_bull_report,
        "read_bear_report": read_bear_report,
        "search_report": search_report,
    }

    task = f"请对比股票 {symbol} 的多空观点，识别共识与分歧，裁决分歧，输出综合分析报告。"
    content, reason = react_loop(MANAGER_SYSTEM_PROMPT, task, tools, max_rounds=6)

    report = run_structured(
        MANAGER_SYSTEM_PROMPT,
        f"根据以下裁决结果生成综合分析报告：\n{content}",
        ComprehensiveReport,
    )

    data = report.model_dump()
    # 评分→评级用确定性规则后置计算，避免 LLM 映射偏差
    data["rating"] = _rating_from_score(data["comprehensive_score"])

    return {"comprehensive_report": data, "exit_reason": reason}
