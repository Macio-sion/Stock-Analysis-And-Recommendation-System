"""舆情分析师 State。"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SentimentAgentState:
    symbol: str
    start_date: str
    end_date: str
    # 节点1输出：原始数据
    social_raw: dict = field(default_factory=dict)
    news_count: Optional[int] = None
    # 节点2输出：NLP 分析
    nlp_results: dict = field(default_factory=dict)
    # 节点3输出：情绪量化
    sentiment: dict = field(default_factory=dict)
    # 节点4输出：最终报告
    sentiment_score: Optional[float] = None
    sentiment_report: dict = field(default_factory=dict)
    # 执行元数据
    node_execution_status: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None
