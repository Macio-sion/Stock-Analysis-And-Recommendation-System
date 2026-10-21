"""基本面分析师 State。"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class FundamentalAgentState:
    ts_code: str
    period: Optional[str] = None
    # 节点1输出：原始数据
    financial_raw: dict = field(default_factory=dict)
    valuation_raw: dict = field(default_factory=dict)
    # 节点2输出：维度评分
    dimension_scores: dict = field(default_factory=dict)
    # 节点3输出：估值判断
    valuation: dict = field(default_factory=dict)
    # 节点4输出：最终报告
    fundamental_score: Optional[float] = None
    fundamental_report: dict = field(default_factory=dict)
    # 执行元数据
    node_execution_status: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None
