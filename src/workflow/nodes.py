"""LangGraph 图节点实现（三阶段）。"""
from __future__ import annotations

from src.agents.bear_researcher import run_bear
from src.agents.bull_researcher import run_bull
from src.agents.fundamental_analyst import run_fundamental_analysis
from src.agents.research_manager import run_manager
from src.agents.sentiment_analyst import run_sentiment_analysis
from src.agents.strategy_executor import run_strategy
from src.agents.technical_analyst import run_technical_analysis
from src.state.stage_merge_state import merge_reports


def technical_node(state: dict) -> dict:
    t = run_technical_analysis(state["ts_code"], state["start_date"], state["end_date"])
    return {"technical_report": t.technical_report, "technical_score": t.technical_score}


def fundamental_node(state: dict) -> dict:
    f = run_fundamental_analysis(state["ts_code"])
    return {"fundamental_report": f.fundamental_report, "fundamental_score": f.fundamental_score}


def sentiment_node(state: dict) -> dict:
    s = run_sentiment_analysis(state["ts_code"], state["start_date"], state["end_date"])
    return {"sentiment_report": s.sentiment_report, "sentiment_score": s.sentiment_score}


def merge_node(state: dict) -> dict:
    merged = merge_reports(
        workflow_id=state["workflow_id"],
        ts_code=state["ts_code"],
        technical_report=state["technical_report"],
        technical_score=state["technical_score"],
        fundamental_report=state["fundamental_report"],
        fundamental_score=state["fundamental_score"],
        sentiment_report=state["sentiment_report"],
        sentiment_score=state["sentiment_score"],
    )
    return {"all_scores": merged.all_scores, "stage_status": merged.stage_status}


def bull_node(state: dict) -> dict:
    return run_bull(
        {
            "symbol": state.get("symbol") or state.get("ts_code", ""),
            "technical_report": state["technical_report"],
            "fundamental_report": state["fundamental_report"],
            "sentiment_report": state["sentiment_report"],
        }
    )


def bear_node(state: dict) -> dict:
    return run_bear(
        {
            "symbol": state.get("symbol") or state.get("ts_code", ""),
            "technical_report": state["technical_report"],
            "fundamental_report": state["fundamental_report"],
            "sentiment_report": state["sentiment_report"],
        }
    )


def manager_node(state: dict) -> dict:
    return run_manager(
        {
            "symbol": state.get("symbol") or state.get("ts_code", ""),
            "bull_report": state["bull_report"],
            "bear_report": state["bear_report"],
            "technical_score": state.get("technical_score", 0),
            "fundamental_score": state.get("fundamental_score", 0),
            "sentiment_score": state.get("sentiment_score", 0),
        }
    )


def strategy_node(state: dict) -> dict:
    return run_strategy(
        {
            "strategy_config": state.get("strategy_config", {}),
            "technical_score": state.get("technical_score", 0),
            "fundamental_score": state.get("fundamental_score", 0),
            "sentiment_score": state.get("sentiment_score", 0),
            "comprehensive_report": state.get("comprehensive_report", {}),
        }
    )
