"""研究员结构化输出模型（多头/空头/研究经理共用子模型）。"""
from typing import Literal

from pydantic import BaseModel, Field


class SupportingArgument(BaseModel):
    """单条支撑论据。"""

    point: str = Field(description="论据的简要描述，一句话概括")
    source: str = Field(description="来源维度：technical / fundamental / sentiment")
    weight: int = Field(ge=1, le=10, description="论据重要程度，1-10 分")
    quote: str = Field(description="从报告中引用的原文，作为论据支撑")


class ConfidenceBreakdown(BaseModel):
    """置信度的多维分解。"""

    evidence_quality: int = Field(ge=0, le=100, description="证据质量评分")
    reasoning_depth: int = Field(ge=0, le=100, description="逻辑深度评分")
    counter_addressed: int = Field(ge=0, le=100, description="反方观点处理程度")
    multi_dimension_consistency: int = Field(ge=0, le=100, description="多维度一致性评分")


class BullishReport(BaseModel):
    """多头研究员最终输出报告。"""

    position: str = Field(default="bullish", description="固定为 bullish")
    summary: str = Field(description="整体看涨观点的精华摘要")
    core_thesis: str = Field(description="核心逻辑链，阐述为什么看涨")
    supporting_arguments: list[SupportingArgument] = Field(description="支撑论据列表，至少 3 条")
    risk_acknowledgment: str = Field(description="风险承认，客观说明负面因素")
    counter_arguments_addressed: list[str] = Field(default_factory=list, description="已回应的反方观点")
    confidence: int = Field(ge=0, le=100, description="综合置信度 0-100")
    confidence_breakdown: ConfidenceBreakdown = Field(description="置信度多维分解")
    key_metrics_highlight: dict = Field(default_factory=dict, description="关键指标速览")
    reasoning_trace: list[str] = Field(default_factory=list, description="推理过程摘要")


class BearishReport(BaseModel):
    """空头研究员最终输出报告。"""

    position: str = Field(default="bearish", description="固定为 bearish")
    summary: str = Field(description="整体看跌观点的精华摘要")
    core_thesis: str = Field(description="核心逻辑链，阐述为什么看跌")
    supporting_arguments: list[SupportingArgument] = Field(description="支撑论据列表，至少 3 条")
    risk_acknowledgment: str = Field(description="风险承认，客观说明正面因素")
    counter_arguments_addressed: list[str] = Field(default_factory=list, description="已回应的反方观点")
    confidence: int = Field(ge=0, le=100, description="综合置信度 0-100")
    confidence_breakdown: ConfidenceBreakdown = Field(description="置信度多维分解")
    key_metrics_highlight: dict = Field(default_factory=dict, description="关键指标速览")
    reasoning_trace: list[str] = Field(default_factory=list, description="推理过程摘要")


class ConsensusPoint(BaseModel):
    """多空双方达成共识的观点。"""

    point: str = Field(description="共识点的简要描述")
    bull_view: str = Field(description="多头对该点的表述")
    bear_view: str = Field(description="空头对该点的表述")
    weight: int = Field(ge=1, le=10, description="共识点重要程度 1-10")


class DebateResolution(BaseModel):
    """对单个分歧点的裁决结果。"""

    point: str = Field(description="分歧点的简要描述")
    winner: str = Field(description="裁决结果：bull / bear / neutral")
    basis: str = Field(description="裁决依据：数据更充分 / 逻辑更合理 / 双方均合理")
    reason: str = Field(description="裁决理由的详细说明")


class ScoreBreakdown(BaseModel):
    """综合评分的多维分解。"""

    technical: int = Field(ge=0, le=100, description="技术面得分")
    fundamental: int = Field(ge=0, le=100, description="基本面得分")
    sentiment: int = Field(ge=0, le=100, description="舆情面得分")
    debate_adjust: int = Field(ge=-20, le=20, description="辩论调整分（可为负）")


class ComprehensiveReport(BaseModel):
    """研究经理最终输出报告。"""

    rating: Literal["强烈看多", "看多", "中性", "看空", "强烈看空"] = Field(description="综合评级")
    summary: str = Field(description="综合分析结论的精华摘要")
    consensus_points: list[ConsensusPoint] = Field(description="多空双方达成共识的观点列表")
    debate_resolutions: list[DebateResolution] = Field(description="对分歧点的裁决结果列表")
    comprehensive_score: int = Field(ge=0, le=100, description="综合评分 0-100")
    score_breakdown: ScoreBreakdown = Field(description="综合评分多维分解")
    core_drivers: list[str] = Field(min_length=1, description="核心驱动因素")
    main_risks: list[str] = Field(min_length=1, description="主要风险点")
    reasoning_trace: list[str] = Field(default_factory=list, description="推理过程摘要")
