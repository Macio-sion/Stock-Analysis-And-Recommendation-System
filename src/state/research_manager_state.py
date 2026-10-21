"""研究经理 State。"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ResearchManagerState:
    workflow_id: str
    ts_code: str
    symbol: str
    bull_report: dict = field(default_factory=dict)
    bear_report: dict = field(default_factory=dict)
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    sentiment_score: float = 0.0
    comprehensive_report: dict = field(default_factory=dict)
    exit_reason: str = ""
    node_execution_status: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
