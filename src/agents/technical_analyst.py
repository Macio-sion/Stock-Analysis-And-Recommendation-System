"""技术分析师（硬编码）：指标计算 → 趋势判断 → 报告生成。"""
from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from src.data.tushare_client import client
from src.persistence import repository
from src.persistence.database import SessionLocal
from src.state.technical_state import TechnicalAgentState


def _last(series: pd.Series, ndigits: int = 2) -> float:
    """取序列最后一个值，NaN 返回 0，并保留指定位数。"""
    v = series.iloc[-1]
    return 0.0 if pd.isna(v) else round(float(v), ndigits)


def _rsi(close: pd.Series, period: int) -> pd.Series:
    """计算 RSI 相对强弱指标。"""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def calc_indicators(raw_ohlcv: pd.DataFrame) -> dict:
    """计算技术指标：MA / MACD / RSI / 布林带 / 成交量 / 关键价位。"""
    close = raw_ohlcv["close"].astype(float)
    high = raw_ohlcv["high"].astype(float)
    low = raw_ohlcv["low"].astype(float)
    vol = raw_ohlcv["vol"].astype(float)

    ma = {
        "ma5": _last(close.rolling(5).mean()),
        "ma10": _last(close.rolling(10).mean()),
        "ma20": _last(close.rolling(20).mean()),
        "ma60": _last(close.rolling(60).mean()),
    }

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    dif = ema12 - ema26
    dea = dif.ewm(span=9, adjust=False).mean()
    macd = {"dif": _last(dif, 3), "dea": _last(dea, 3), "macd": _last(dif - dea, 3)}

    rsi = {f"rsi{n}": _last(_rsi(close, n), 1) for n in (6, 12, 24)}

    mid = close.rolling(20).mean()
    std = close.rolling(20).std()
    bb = {
        "upper": _last(mid + 2 * std),
        "middle": _last(mid),
        "lower": _last(mid - 2 * std),
    }

    volume_ratio = round(float(vol.iloc[-1] / vol.rolling(5).mean().iloc[-1]), 2)
    obv = float((np.sign(close.diff()).fillna(0) * vol).cumsum().iloc[-1])
    vol_ind = {"volume_ratio": volume_ratio, "obv": round(obv, 0)}

    key_levels = {
        "support": round(float(low.tail(20).min()), 2),
        "resistance": round(float(high.tail(20).max()), 2),
    }

    return {"ma": ma, "macd": macd, "rsi": rsi, "bb": bb, "vol": vol_ind, "key_levels": key_levels}


def judge_trend(indicators: dict) -> dict:
    """根据指标统计多空信号，判断趋势方向与强度。"""
    ma = indicators["ma"]
    macd = indicators["macd"]
    rsi = indicators["rsi"]
    bb = indicators["bb"]
    vol = indicators["vol"]

    buy = sell = neutral = 0

    if ma["ma5"] > ma["ma20"] > ma["ma60"]:
        buy += 1
    elif ma["ma5"] < ma["ma20"] < ma["ma60"]:
        sell += 1
    else:
        neutral += 1

    if macd["dif"] > macd["dea"]:
        buy += 1
    elif macd["dif"] < macd["dea"]:
        sell += 1
    else:
        neutral += 1

    if rsi["rsi6"] > 70:
        sell += 1
    elif rsi["rsi6"] < 30:
        buy += 1
    else:
        neutral += 1

    if ma["ma20"] > bb["middle"]:
        buy += 1
    else:
        sell += 1

    if vol["volume_ratio"] > 1.5:
        buy += 1
    else:
        neutral += 1

    if buy > sell:
        trend = "上涨"
    elif sell > buy:
        trend = "下跌"
    else:
        trend = "震荡"

    total = buy + sell + neutral
    strength = int(buy / total * 100) if total else 50

    return {
        "trend": trend,
        "strength": strength,
        "key_levels": indicators["key_levels"],
        "signal_summary": {
            "buy_signals": buy,
            "sell_signals": sell,
            "neutral_signals": neutral,
        },
    }


def gen_technical_report(trend_analysis: dict, technical_score: float) -> dict:
    """生成技术分析报告。"""
    trend = trend_analysis["trend"]
    if trend == "上涨":
        summary = "均线呈多头排列，MACD 与 RSI 偏强，短期趋势向上。"
    elif trend == "下跌":
        summary = "均线呈空头排列，MACD 与 RSI 偏弱，短期趋势向下。"
    else:
        summary = "多空信号交织，趋势方向不明，处于震荡整理。"

    macd_signal = "金叉" if trend_analysis["signal_summary"]["buy_signals"] >= 3 else "死叉"
    return {
        "score": technical_score,
        "trend": trend,
        "summary": summary,
        "key_metrics": {
            "rsi6": 0.0,
            "macd_signal": macd_signal,
        },
        "key_levels": trend_analysis["key_levels"],
    }


def run_technical_analysis(ts_code: str, start_date: str, end_date: str, workflow_id: str | None = None) -> TechnicalAgentState:
    """完整执行技术分析并落库快照。"""
    state = TechnicalAgentState(ts_code=ts_code, start_date=start_date, end_date=end_date)
    state.started_at = datetime.utcnow()

    state.raw_ohlcv = client.get_daily(ts_code, start_date, end_date)
    state.data_record_count = len(state.raw_ohlcv)
    state.indicators = calc_indicators(state.raw_ohlcv)
    state.trend_analysis = judge_trend(state.indicators)

    sig = state.trend_analysis["signal_summary"]
    state.technical_score = round(max(0.0, min(100.0, 50 + (sig["buy_signals"] - sig["sell_signals"]) * 10)), 1)
    state.technical_report = gen_technical_report(state.trend_analysis, state.technical_score)
    state.technical_report["key_metrics"]["rsi6"] = state.indicators["rsi"]["rsi6"]

    state.completed_at = datetime.utcnow()
    state.node_execution_status = {
        "data_fetch": "success",
        "indicator_calc": "success",
        "trend_judge": "success",
        "report_gen": "success",
    }

    if workflow_id:
        db = SessionLocal()
        try:
            repository.save_snapshot(
                db,
                workflow_id,
                "technical",
                {"technical_score": state.technical_score, "technical_report": state.technical_report},
                phase="stage1",
            )
        finally:
            db.close()

    return state
