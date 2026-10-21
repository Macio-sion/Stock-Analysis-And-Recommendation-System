"""代码生成与沙箱执行引擎 State。"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CodeGenSandboxState:
    workflow_id: str
    ts_code: str
    symbol: str
    algorithm_description: str
    comprehensive_report: dict = field(default_factory=dict)
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    sentiment_score: float = 0.0
    # 代码生成阶段
    parsed_spec: dict = field(default_factory=dict)
    generated_code: dict = field(default_factory=dict)
    ast_validation: dict = field(default_factory=dict)
    # 沙箱执行阶段
    container_id: Optional[str] = None
    compile_result: dict = field(default_factory=dict)
    execution_result: dict = field(default_factory=dict)
    logs: list = field(default_factory=list)
    metric_series: list = field(default_factory=list)
    # 执行元数据
    node_execution_status: dict = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None
    total_tokens_used: Optional[int] = None
