"""多头研究员（ReAct）：收集看涨论据 → 输出 BullishReport。"""
from __future__ import annotations

from config.prompts.bull_researcher import BULL_SYSTEM_PROMPT
from src.agents.researcher_models import BullishReport
from src.llm.react_engine import react_loop, run_structured
from src.tools.report_readers import make_report_readers
from src.tools.search_tools import make_search_tool


def run_bull(state: dict) -> dict:
    """多头研究员节点。

    Args:
        state: 含 technical_report / fundamental_report / sentiment_report / symbol

    Returns:
        {"bull_report": dict, "exit_reason": str}
    """
    tech = state["technical_report"]
    fund = state["fundamental_report"]
    sent = state["sentiment_report"]
    symbol = state.get("symbol") or state.get("ts_code", "")

    tools = make_report_readers(tech, fund, sent)
    tools["search_report"] = make_search_tool(tech, fund, sent)

    task = f"请分析股票 {symbol} 的看涨论据，用工具读取报告并收集至少 3 条看涨证据。"
    content, reason = react_loop(BULL_SYSTEM_PROMPT, task, tools, max_rounds=6)

    report = run_structured(
        BULL_SYSTEM_PROMPT,
        f"根据以下收集到的看涨论据，生成多头观点报告：\n{content}",
        BullishReport,
    )

    return {"bull_report": report.model_dump(), "exit_reason": reason}
