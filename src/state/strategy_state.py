"""策略执行 State。"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class StrategyAgentState:
    workflow_id: str
    ts_code: str
    symbol: str
    comprehensive_report: dict = field(default_factory=dict)
    strategy_config: dict = field(default_factory=dict)
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    sentiment_score: float = 0.0
    strategy: dict = field(default_factory=dict)
    scoring: dict = field(default_factory=dict)
    recommendation: dict = field(default_factory=dict)
    final_report: dict = field(default_factory=dict)
    node_execution_status: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
