"""基本面分析师（硬编码）：维度评分 → 估值判断 → 报告生成。"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from src.data.tushare_client import client
from src.persistence import repository
from src.persistence.database import SessionLocal
from src.state.fundamental_state import FundamentalAgentState


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _row_value(df: pd.DataFrame, col: str, default: float = 0.0) -> float:
    """安全读取 DataFrame 首行某列，缺失或异常返回默认值。"""
    if df is None or df.empty or col not in df.columns:
        return default
    v = df.iloc[0][col]
    try:
        return float(v) if pd.notna(v) else default
    except (TypeError, ValueError):
        return default


def build_financial_raw(df: pd.DataFrame) -> dict:
    """从 fina_indicator 结果提取财务核心指标。"""
    return {
        "roe": _row_value(df, "roe"),
        "gross_margin": _row_value(df, "gross_margin"),
        "netprofit_margin": _row_value(df, "netprofit_margin"),
        "tr_yoy": _row_value(df, "tr_yoy"),
        "netprofit_yoy": _row_value(df, "netprofit_yoy"),
        "debt_to_assets": _row_value(df, "debt_to_assets"),
        "current_ratio": _row_value(df, "current_ratio"),
    }


def build_valuation_raw(df: pd.DataFrame) -> dict:
    """从 daily_basic 结果提取估值指标。"""
    return {
        "pe": _row_value(df, "pe"),
        "pb": _row_value(df, "pb"),
        "ps": _row_value(df, "ps"),
    }


def calc_dimension_scores(financial_raw: dict) -> dict:
    """计算盈利能力 / 成长能力 / 财务健康三个维度评分。"""
    roe = financial_raw.get("roe", 0)
    gross_margin = financial_raw.get("gross_margin", 0)
    tr_yoy = financial_raw.get("tr_yoy", 0)
    netprofit_yoy = financial_raw.get("netprofit_yoy", 0)
    debt_to_assets = financial_raw.get("debt_to_assets", 0)
    current_ratio = financial_raw.get("current_ratio", 0)

    profit = _clamp(roe / 20 * 60 + gross_margin / 40 * 40)
    growth = _clamp(tr_yoy / 30 * 50 + netprofit_yoy / 30 * 50)
    health = _clamp((100 - debt_to_assets) * 0.6 + min(current_ratio / 2, 1) * 40)

    return {
        "profit": round(profit, 1),
        "growth": round(growth, 1),
        "health": round(health, 1),
        "combined": round((profit + growth + health) / 3, 1),
    }


def judge_valuation(valuation_raw: dict) -> dict:
    """根据 PE 判断估值状态（低估 / 合理 / 高估）。"""
    pe = valuation_raw.get("pe", 0)
    pb = valuation_raw.get("pb", 0)

    if pe <= 0:
        status = "合理"
    elif pe < 15:
        status = "低估"
    elif pe < 30:
        status = "合理"
    else:
        status = "高估"

    return {
        "status": status,
        "pe": round(pe, 2),
        "pb": round(pb, 2),
        "pe_percentile": None,
        "industry_pe_avg": None,
        "valuation_gap": None,
    }


def gen_fundamental_report(financial_raw: dict, dimension_scores: dict, valuation: dict) -> dict:
    """生成基本面分析报告。"""
    strengths: list[str] = []
    risks: list[str] = []

    if dimension_scores["profit"] >= 60:
        strengths.append("盈利能力稳健")
    if dimension_scores["growth"] >= 60:
        strengths.append("成长能力较强")
    if dimension_scores["health"] >= 60:
        strengths.append("财务结构健康")
    else:
        risks.append("资产负债率偏高")

    if valuation["status"] == "低估":
        strengths.append("估值具有安全边际")
    elif valuation["status"] == "高估":
        risks.append("估值偏高")

    val_factor = 60 if valuation["status"] == "低估" else 50 if valuation["status"] == "合理" else 40
    score = round(dimension_scores["combined"] * 0.7 + val_factor * 0.3, 1)

    return {
        "score": score,
        "valuation_status": valuation["status"],
        "summary": f"基本面综合评分 {score}，当前估值{valuation['status']}。",
        "metrics": {
            "roe": financial_raw.get("roe", 0),
            "pe": valuation["pe"],
            "debt_ratio": financial_raw.get("debt_to_assets", 0),
        },
        "strengths": strengths,
        "risks": risks,
    }


def run_fundamental_analysis(
    ts_code: str,
    period: str | None = None,
    start_date: str = "20250101",
    end_date: str = "20260831",
    workflow_id: str | None = None,
) -> FundamentalAgentState:
    """完整执行基本面分析并落库快照。"""
    state = FundamentalAgentState(ts_code=ts_code, period=period)
    state.started_at = datetime.utcnow()

    fina_df = client.get_fina_indicator(ts_code, period=period)
    basic_df = client.get_daily_basic(ts_code, start_date, end_date)

    state.financial_raw = build_financial_raw(fina_df)
    state.valuation_raw = build_valuation_raw(basic_df)
    state.dimension_scores = calc_dimension_scores(state.financial_raw)
    state.valuation = judge_valuation(state.valuation_raw)
    state.fundamental_report = gen_fundamental_report(state.financial_raw, state.dimension_scores, state.valuation)
    state.fundamental_score = state.fundamental_report["score"]

    state.completed_at = datetime.utcnow()
    state.node_execution_status = {
        "data_fetch": "success",
        "dimension_score": "success",
        "valuation_judge": "success",
        "report_gen": "success",
    }

    if workflow_id:
        db = SessionLocal()
        try:
            repository.save_snapshot(
                db,
                workflow_id,
                "fundamental",
                {"fundamental_score": state.fundamental_score, "fundamental_report": state.fundamental_report},
                phase="stage1",
            )
        finally:
            db.close()

    return state
