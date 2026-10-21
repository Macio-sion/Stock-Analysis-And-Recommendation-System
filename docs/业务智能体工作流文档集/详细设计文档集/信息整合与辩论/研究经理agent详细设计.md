# 研究经理agent详细设计

## 工具集tools详细
tool1: 读取多头观点报告
```python
def read_bull_report(state: ResearchManagerState) -> dict:
    """
    读取多头观点报告，用于处理多空辩论中的多头观点
    params:
        state: ResearchManagerState
    Returns:
        dict: 包含多头观点信息的字典
    """
```
tool2: 读取空头观点报告
```python
def read_bear_report(state: ResearchManagerState) -> dict:
    """
    读取空头观点报告，用于处理多空辩论中的空头观点
    params:
        state: ResearchManagerState
    Returns:
        dict: 包含空头观点信息的字典
    """
```
tool3: 在观点报告中按关键词搜索相关内容
```python
def search_report(report_content: dict, keyword: str) -> dict:
    """
    在观点报告中按关键词搜索相关内容，用于定位特定维度的论据
    params:
        report_content: 报告内容字典
        keyword: 搜索关键词（如"ROE"、"金叉"、"减持"）
    Returns:
        dict: 包含相关内容结果的字典
    """
```
## 结构化输出structure output详细
```python
# ============================================================
# 子模型：共识点
# ============================================================
class ConsensusPoint(BaseModel):
    """多空双方达成共识的观点"""
    point: str = Field(
        description="共识点的简要描述"
    )
    bull_view: str = Field(
        description="多头对该点的表述"
    )
    bear_view: str = Field(
        description="空头对该点的表述"
    )
    weight: int = Field(
        ge=1, le=10,
        description="共识点的重要程度，1-10分"
    )
# ============================================================
# 子模型：分歧裁决
# ============================================================
class DebateResolution(BaseModel):
    """对单个分歧点的裁决结果"""
    point: str = Field(
        description="分歧点的简要描述"
    )
    winner: str = Field(
        description="裁决结果，可选值: bull / bear / neutral"
    )
    basis: str = Field(
        description="裁决依据，可选值: 数据更充分 / 逻辑更合理 / 双方均合理"
    )
    reason: str = Field(
        description="裁决理由的详细说明"
    )
# ============================================================
# 子模型：综合评分分解
# ============================================================
class ScoreBreakdown(BaseModel):
    """综合评分的多维分解"""
    technical: float = Field(ge=0, le=100, description="技术面得分")
    fundamental: float = Field(ge=0, le=100, description="基本面得分")
    sentiment: float = Field(ge=0, le=100, description="舆情面得分")
    debate_adjust: float = Field(ge=-20, le=20, description="辩论调整分（可为负）")
# ============================================================
# 主模型：综合分析报告
# ============================================================
class ComprehensiveReport(BaseModel):
    """研究经理Agent的最终输出报告"""
    
    # 1. 综合评级
    rating: str = Field(
        description="综合评级，可选值: 强烈看多 / 看多 / 中性 / 看空 / 强烈看空"
    )
    
    # 2. 核心结论
    summary: str = Field(
        min_length=50, max_length=300,
        description="综合分析结论的精华摘要，供下游快速了解"
    )
    
    # 3. 多空对比结果
    consensus_points: List[ConsensusPoint] = Field(
        description="多空双方达成共识的观点列表"
    )
    debate_resolutions: List[DebateResolution] = Field(
        description="对分歧点的裁决结果列表"
    )
    
    # 4. 综合评分
    comprehensive_score: float = Field(
        ge=0, le=100,
        description="综合评分，0-100分"
    )
    score_breakdown: ScoreBreakdown = Field(
        description="综合评分的多维分解"
    )
    
    # 5. 关键结论
    core_drivers: List[str] = Field(
        default_factory=list,
        description="核心驱动因素列表，影响股价的核心正面因素"
    )
    main_risks: List[str] = Field(
        default_factory=list,
        description="主要风险点列表，需要关注的负面因素"
    )
    
    # 6. 推理过程摘要
    reasoning_trace: List[str] = Field(
        default_factory=list,
        description="简要的推理过程记录，便于审计"
    )
```
上述仅供参考，实际实现中可能需要根据具体需求进行调整。
## state参数解析
### 输入参数
```python
workflow_id: str
ts_code: str
symbol: str
bull_report: Dict[str, Any] = field(default_factory=dict)
bear_report: Dict[str, Any] = field(default_factory=dict)
technical_score: float = 0.0
fundamental_score: float = 0.0
sentiment_score: float = 0.0
```
字段	类型	业务含义	对后续节点/系统的作用
workflow_id	str	工作流唯一标识	贯穿全流程，用于日志关联和状态查询
ts_code	str	Tushare标准股票代码	业务主键：告诉研究经理"分析的是哪只股票"
symbol	str	用户友好的股票代码	用于最终报告展示，让用户读懂
bull_report	Dict	多头研究员的完整输出报告	辩论素材：研究经理从中提取多头观点与论据
bear_report	Dict	空头研究员的完整输出报告	辩论素材：研究经理从中提取空头观点与论据
technical_score	float	技术面综合得分（0-100）	参考值：用于综合评分的技术维度
fundamental_score	float	基本面综合得分（0-100）	参考值：用于综合评分的基本面维度
sentiment_score	float	舆情综合得分（0-100）	参考值：用于综合评分的舆情维度
#### ReAct循环状态
```python
reasoning_round: int = 0
max_rounds: int = 6
is_complete: bool = False
exit_reason: Optional[str] = None
```
字段	取值范围	业务含义	对后续节点/系统的作用
reasoning_round	0 → N	当前已执行的推理轮次	循环控制：让引擎知道当前是第几轮，防止无限循环
max_rounds	固定6	最大允许的推理轮次上限	安全阀：强制停止以保护系统资源
is_complete	True/False	推理是否已完成	流程控制：阶段三启动前检查此字段，确保研究经理已完成裁决
exit_reason	max_rounds/debate_resolved/confidence_high/llm_finish	记录因何原因退出循环	可观测性：便于调试优化
#### 思考链记录
```python
thought_history: List[Dict[str, Any]] = field(default_factory=list)
```
字段	业务含义	对后续节点/系统的作用
thought_history	记录ReAct循环中每一轮的"思考→行动→观察"过程	可审计性：追溯研究经理的裁决过程，判断其逻辑是否合理
#### 共识与分歧记录
```python
consensus_points: List[Dict[str, Any]] = field(default_factory=list)
divergence_points: List[Dict[str, Any]] = field(default_factory=list)
debate_resolutions: List[Dict[str, Any]] = field(default_factory=list)
```
字段	业务含义	对后续节点/系统的作用
consensus_points	多空双方达成共识的观点	共识加权：共识点越多，综合结论越可靠
divergence_points	多空双方存在分歧的观点	辩论对象：研究经理需逐一裁决
debate_resolutions	对分歧点的裁决结果	裁决输出：决定综合评分的方向与调整幅度
#### 综合评分与评级
```python
comprehensive_score: float = 0.0
score_breakdown: Dict[str, float] = field(default_factory=dict)
rating: Optional[str] = None
```
字段	业务含义	对后续节点/系统的作用
comprehensive_score	综合评分（0-100）	阶段三策略执行的核心输入
score_breakdown	评分分解（技术/基本面/舆情/辩论调整）	可解释性：让用户理解分数构成
rating	综合评级（强烈看多/看多/中性/看空/强烈看空）	报告结论，供最终推荐引用
#### 综合分析报告
```python
comprehensive_report: Optional[Dict[str, Any]] = field(default_factory=dict)
```
字段	业务含义	对后续节点/系统的作用
comprehensive_report	研究经理的最终输出报告，包含评级、摘要、共识与分歧、综合评分等完整内容	阶段三策略执行agent的直接输入

comprehensive_report 内部结构已在之前的结构化输出设计中详细定义，包含：

子字段	对阶段三/系统的作用
rating	作为最终推荐的定性参考
summary	拼入最终推荐理由
consensus_points	体现多空共识，增强结论可信度
debate_resolutions	体现裁决过程，增强可解释性
comprehensive_score	阶段三加权与阈值比较的核心输入
core_drivers / main_risks	用于生成推荐理由与风险提示
### 元数据
```python
node_execution_status: Dict[str, str] = field(default_factory=dict)
error_message: Optional[str] = None
started_at: Optional[datetime] = None
completed_at: Optional[datetime] = None
execution_duration_ms: Optional[int] = None
total_tokens_used: Optional[int] = None
```
字段	业务含义	对后续节点/系统的作用
node_execution_status	记录各执行阶段的状态（success/failed）	流程控制：阶段三启动前检查此字段
error_message	具体的错误信息	调试：持久化后可追溯失败原因
started_at / completed_at	起止时间	性能监控：记录研究经理ReAct循环耗时
execution_duration_ms	总执行耗时	成本/性能分析：ReAct循环通常较慢，便于评估优化空间
total_tokens_used	LLM调用的Token消耗总量	成本监控：研究经理是LLM密集型的，便于控制预算
