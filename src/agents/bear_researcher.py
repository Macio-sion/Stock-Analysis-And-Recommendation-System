"""空头研究员（ReAct）：收集看跌论据 → 输出 BearishReport。"""
from __future__ import annotations

from config.prompts.bear_researcher import BEAR_SYSTEM_PROMPT
from src.agents.researcher_models import BearishReport
from src.llm.react_engine import react_loop, run_structured
from src.tools.report_readers import make_report_readers
from src.tools.search_tools import make_search_tool


def run_bear(state: dict) -> dict:
    """空头研究员节点。

    Args:
        state: 含 technical_report / fundamental_report / sentiment_report / symbol

    Returns:
        {"bear_report": dict, "exit_reason": str}
    """
    tech = state["technical_report"]
    fund = state["fundamental_report"]
    sent = state["sentiment_report"]
    symbol = state.get("symbol") or state.get("ts_code", "")

    tools = make_report_readers(tech, fund, sent)
    tools["search_report"] = make_search_tool(tech, fund, sent)

    task = f"请分析股票 {symbol} 的看跌论据，用工具读取报告并收集至少 3 条看跌证据。"
    content, reason = react_loop(BEAR_SYSTEM_PROMPT, task, tools, max_rounds=6)

    report = run_structured(
        BEAR_SYSTEM_PROMPT,
        f"根据以下收集到的看跌论据，生成空头观点报告：\n{content}",
        BearishReport,
    )

    return {"bear_report": report.model_dump(), "exit_reason": reason}
