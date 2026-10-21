"""舆情分析师（硬编码）：数据采集 → 情感分析 → 情绪量化 → 报告生成。

数据源为 akshare（东方财富个股新闻），无现成情感标签，
采用关键词词典做基础情感分析，后续阶段可替换为 LLM 情感分析。
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime

from src.data.sentiment_client import fetch_sentiment
from src.persistence import repository
from src.persistence.database import SessionLocal
from src.state.sentiment_state import SentimentAgentState

POSITIVE_WORDS = ["增长", "上涨", "超预期", "盈利", "利好", "突破", "回购", "增持", "中标", "创新高", "扭亏", "分红"]
NEGATIVE_WORDS = ["下降", "下跌", "亏损", "减持", "风险", "违规", "处罚", "下滑", "爆雷", "退市", "诉讼", "质押"]


def _sentiment_of(text: str) -> str:
    """基于关键词词典的简单情感判断。"""
    pos = sum(1 for w in POSITIVE_WORDS if w in text)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


def build_social_raw(data: dict) -> dict:
    """fetch_sentiment 已返回 news_list，这里直接透传。"""
    return {"news_list": data.get("news_list", [])}


def nlp_analyze(social_raw: dict) -> dict:
    """对每条新闻做关键词情感分析，产出 sentiments / entities / topics。"""
    sentiments = []
    for news in social_raw.get("news_list", []):
        text = f"{news.get('title', '')} {news.get('content', '')}"
        sentiments.append(
            {
                "text": news.get("title", ""),
                "sentiment": _sentiment_of(text),
                "score": 0.5,
            }
        )
    topics = {"新闻": len(sentiments)}
    return {"sentiments": sentiments, "entities": [], "topics": topics}


def quantify_sentiment(nlp_results: dict) -> dict:
    """统计情感分布，计算情绪得分与热度。"""
    sentiments = nlp_results.get("sentiments", [])
    total = len(sentiments)
    if total == 0:
        return {
            "sentiment_score": 50.0,
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "heat_score": 0.0,
            "polarity": "中性",
        }

    pos = neg = neu = 0
    for s in sentiments:
        if s["sentiment"] == "positive":
            pos += 1
        elif s["sentiment"] == "negative":
            neg += 1
        else:
            neu += 1

    sentiment_score = round((pos - neg) / total * 100 + 50, 1)
    heat_score = round(min(100.0, total * 10), 1)
    polarity = "积极" if sentiment_score > 60 else "消极" if sentiment_score < 40 else "中性"

    return {
        "sentiment_score": sentiment_score,
        "sentiment_distribution": {
            "positive": round(pos / total * 100),
            "neutral": round(neu / total * 100),
            "negative": round(neg / total * 100),
        },
        "heat_score": heat_score,
        "polarity": polarity,
    }


def gen_sentiment_report(social_raw: dict, sentiment: dict) -> dict:
    """生成舆情分析报告。"""
    news_list = social_raw.get("news_list", [])
    key_events = [n["title"] for n in news_list[:5]]
    risk_factors = [n["title"] for n in news_list if _sentiment_of(f"{n.get('title','')} {n.get('content','')}") == "negative"][:3]
    hot_topics = ["个股新闻"]

    polarity = sentiment["polarity"]
    summary = f"近期舆情整体{polarity}，共采集 {len(news_list)} 条新闻。"

    return {
        "score": sentiment["sentiment_score"],
        "polarity": polarity,
        "summary": summary,
        "key_events": key_events,
        "hot_topics": hot_topics,
        "risk_factors": risk_factors,
    }


def run_sentiment_analysis(symbol: str, start_date: str, end_date: str, workflow_id: str | None = None) -> SentimentAgentState:
    """完整执行舆情分析并落库快照。"""
    state = SentimentAgentState(symbol=symbol, start_date=start_date, end_date=end_date)
    state.started_at = datetime.utcnow()

    data = fetch_sentiment(symbol, start_date, end_date)
    state.social_raw = build_social_raw(data)
    state.news_count = len(state.social_raw["news_list"])
    state.nlp_results = nlp_analyze(state.social_raw)
    state.sentiment = quantify_sentiment(state.nlp_results)
    state.sentiment_score = state.sentiment["sentiment_score"]
    state.sentiment_report = gen_sentiment_report(state.social_raw, state.sentiment)

    state.completed_at = datetime.utcnow()
    state.node_execution_status = {
        "data_collect": "success",
        "nlp_analysis": "success",
        "sentiment_quantify": "success",
        "report_gen": "success",
    }

    if workflow_id:
        db = SessionLocal()
        try:
            repository.save_snapshot(
                db,
                workflow_id,
                "sentiment",
                {"sentiment_score": state.sentiment_score, "sentiment_report": state.sentiment_report},
                phase="stage1",
            )
        finally:
            db.close()

    return state
