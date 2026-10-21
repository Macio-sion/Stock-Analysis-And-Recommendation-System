"""阶段一汇聚 State 与汇总节点。"""
from dataclasses import dataclass, field


@dataclass
class StageOneMergeState:
    """阶段一汇聚后的状态。"""

    workflow_id: str
    ts_code: str
    technical_report: dict = field(default_factory=dict)
    fundamental_report: dict = field(default_factory=dict)
    sentiment_report: dict = field(default_factory=dict)
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    sentiment_score: float = 0.0
    all_scores: dict = field(default_factory=dict)
    total_duration_ms: int | None = None
    stage_status: str = "completed"
    errors: list = field(default_factory=list)


def merge_reports(
    workflow_id: str,
    ts_code: str,
    technical_report: dict,
    technical_score: float,
    fundamental_report: dict,
    fundamental_score: float,
    sentiment_report: dict,
    sentiment_score: float,
) -> StageOneMergeState:
    """汇聚三份报告与三维度得分。"""
    return StageOneMergeState(
        workflow_id=workflow_id,
        ts_code=ts_code,
        technical_report=technical_report,
        fundamental_report=fundamental_report,
        sentiment_report=sentiment_report,
        technical_score=technical_score,
        fundamental_score=fundamental_score,
        sentiment_score=sentiment_score,
        all_scores={
            "technical": technical_score,
            "fundamental": fundamental_score,
            "sentiment": sentiment_score,
        },
    )
