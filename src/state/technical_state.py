"""技术分析师 State。"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd


@dataclass
class TechnicalAgentState:
    ts_code: str
    start_date: str
    end_date: str
    # 节点1输出：原始数据
    raw_ohlcv: Optional[pd.DataFrame] = None
    data_record_count: Optional[int] = None
    # 节点2输出：技术指标
    indicators: dict = field(default_factory=dict)
    # 节点3输出：趋势判断
    trend_analysis: dict = field(default_factory=dict)
    # 节点4输出：最终报告
    technical_score: Optional[float] = None
    technical_report: dict = field(default_factory=dict)
    # 执行元数据
    node_execution_status: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None
