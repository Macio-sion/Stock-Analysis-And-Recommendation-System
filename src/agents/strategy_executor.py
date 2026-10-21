"""策略执行器（硬编码）：策略匹配 → 评分计算 → 推荐决策 → 报告生成。"""
from __future__ import annotations

STRATEGY_WEIGHTS = {
    "价值型": {"fundamental": 0.7, "technical": 0.2, "sentiment": 0.1},
    "成长型": {"fundamental": 0.5, "technical": 0.3, "sentiment": 0.2},
    "技术型": {"technical": 0.6, "fundamental": 0.2, "sentiment": 0.2},
    "情绪型": {"sentiment": 0.5, "technical": 0.3, "fundamental": 0.2},
    "均衡型": {"fundamental": 0.34, "technical": 0.33, "sentiment": 0.33},
}


def match_strategy(strategy_type: str, custom_weights: dict | None = None) -> dict:
    """识别策略类型，加载各维度权重。"""
    if strategy_type == "自定义":
        return custom_weights or STRATEGY_WEIGHTS["均衡型"]
    return STRATEGY_WEIGHTS.get(strategy_type, STRATEGY_WEIGHTS["均衡型"])


def calc_score(weights: dict, scores: dict) -> dict:
    """按权重加权计算综合得分，并给出置信区间。"""
    weighted = 0.0
    for key in ("technical", "fundamental", "sentiment"):
        weighted += weights.get(key, 0) * scores.get(key, 0)
    weighted_score = round(weighted, 1)
    confidence_interval = [
        round(max(0.0, weighted_score - 5), 1),
        round(min(100.0, weighted_score + 5), 1),
    ]
    return {
        "weighted_score": weighted_score,
        "confidence_interval": confidence_interval,
        "benchmark_diff": None,
    }


def decide(score: float) -> dict:
    """根据综合得分阈值输出推荐动作。"""
    if score >= 70:
        action = "买入"
    elif score >= 40:
        action = "持有/观望"
    else:
        action = "回避"
    return {"action": action, "score": score, "confidence": "中", "reasons": []}


def run_strategy(state: dict) -> dict:
    """策略执行节点：完整流程。

    Args:
        state: 含 strategy_config / 三维度得分 / comprehensive_report

    Returns:
        {"strategy": ..., "scoring": ..., "recommendation": ..., "final_report": ...}
    """
    strategy_config = state.get("strategy_config", {})
    strategy_type = strategy_config.get("strategy_type", "均衡型")
    custom_weights = strategy_config.get("weights")

    scores = {
        "technical": state.get("technical_score", 0),
        "fundamental": state.get("fundamental_score", 0),
        "sentiment": state.get("sentiment_score", 0),
    }

    weights = match_strategy(strategy_type, custom_weights)
    scoring = calc_score(weights, scores)
    recommendation = decide(scoring["weighted_score"])

    report = state.get("comprehensive_report", {})
    rating = report.get("rating", "")
    recommendation["reasons"] = [
        f"策略类型：{strategy_type}",
        f"加权综合得分：{scoring['weighted_score']}",
    ]
    if rating:
        recommendation["reasons"].append(f"综合评级：{rating}")

    final_report = {
        "action": recommendation["action"],
        "score": scoring["weighted_score"],
        "rating": rating,
        "reasons": recommendation["reasons"],
        "risk_tips": report.get("main_risks", []),
    }

    return {
        "strategy": {"strategy_type": strategy_type, "weights": weights},
        "scoring": scoring,
        "recommendation": recommendation,
        "final_report": final_report,
    }
