"""LangGraph 图定义（三阶段编排）。"""
from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.workflow.nodes import (
    bear_node,
    bull_node,
    fundamental_node,
    manager_node,
    merge_node,
    sentiment_node,
    strategy_node,
    technical_node,
)


class StageOneGraphState(TypedDict, total=False):
    workflow_id: str
    ts_code: str
    symbol: str
    start_date: str
    end_date: str
    strategy_config: dict
    technical_report: dict
    technical_score: float
    fundamental_report: dict
    fundamental_score: float
    sentiment_report: dict
    sentiment_score: float
    all_scores: dict
    stage_status: str
    bull_report: dict
    bear_report: dict
    comprehensive_report: dict
    strategy: dict
    scoring: dict
    recommendation: dict
    final_report: dict


def build_graph():
    """构建三阶段编排图：阶段一并行分析 → 阶段二多空辩论 → 阶段三策略执行。"""
    builder = StateGraph(StageOneGraphState)

    # 阶段一：三分析师并行 + 汇聚
    builder.add_node("technical", technical_node)
    builder.add_node("fundamental", fundamental_node)
    builder.add_node("sentiment", sentiment_node)
    builder.add_node("merge", merge_node)

    # 阶段二：多头/空头并行 + 研究经理
    builder.add_node("bull", bull_node)
    builder.add_node("bear", bear_node)
    builder.add_node("manager", manager_node)

    # 阶段三：策略执行
    builder.add_node("strategy", strategy_node)

    # 阶段一连接
    builder.add_edge(START, "technical")
    builder.add_edge(START, "fundamental")
    builder.add_edge(START, "sentiment")
    builder.add_edge("technical", "merge")
    builder.add_edge("fundamental", "merge")
    builder.add_edge("sentiment", "merge")

    # 阶段二连接
    builder.add_edge("merge", "bull")
    builder.add_edge("merge", "bear")
    builder.add_edge("bull", "manager")
    builder.add_edge("bear", "manager")

    # 阶段三连接
    builder.add_edge("manager", "strategy")
    builder.add_edge("strategy", END)

    return builder.compile()


graph = build_graph()
