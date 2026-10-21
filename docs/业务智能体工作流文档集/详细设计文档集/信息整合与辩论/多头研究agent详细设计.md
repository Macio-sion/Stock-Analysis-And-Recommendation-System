# 多头研究agent详细设计

## 工具集tools详细
tool1: 读取技术报告
```python
def read_technical_report(state: BullishAgentState) -> dict:
    """
    读取技术报告，用于处理StageOneMergeState中的技术报告
    params:
        state: BullishAgentState
    Returns:
        dict: 包含技术面信息的字典
    """
```
tool2: 读取基本面报告
```python
def read_fundamental_report(state: BullishAgentState) -> dict:
    """
    读取基本面报告，用于处理StageOneMergeState中的基本面报告
    params:
        state: BullishAgentState
    Returns:
        dict: 包含基本面面信息的字典
    """
```
tool3: 读取舆情报告
```python
def read_sentiment_report(state: BullishAgentState) -> dict:
    """
    读取舆情报告，用于处理StageOneMergeState中的舆情报告
    params:
        state: BullishAgentState
    Returns:
        dict: 包含舆情面信息的字典
    """
```
## 结构化输出structure output详细
```python
# ============================================================
# 子模型：支撑论据
# ============================================================
class SupportingArgument(BaseModel):
    """单条支撑论据的结构"""
    point: str = Field(
        description="论据的简要描述，一句话概括"
    )
    source: str = Field(
        description="来源维度，可选值: technical / fundamental / sentiment"
    )
    weight: int = Field(
        ge=1, le=10,
        description="论据的重要程度，1-10分，10分为最重要"
    )
    quote: str = Field(
        description="从报告中引用的原始内容，作为论据的支撑"
    )
# ============================================================
# 子模型：置信度分解
# ============================================================
class ConfidenceBreakdown(BaseModel):
    """置信度的多维分解"""
    evidence_quality: int = Field(ge=0, le=100, description="证据质量评分")
    reasoning_depth: int = Field(ge=0, le=100, description="逻辑深度评分")
    counter_addressed: int = Field(ge=0, le=100, description="反方观点处理程度")
    multi_dimension_consistency: int = Field(ge=0, le=100, description="多维度一致性评分")
# ============================================================
# 主模型：多头观点报告
# ============================================================
class BullishReport(BaseModel):
    """多头研究员Agent的最终输出报告"""
    
    # 1. 基本信息
    position: str = Field(
        default="bullish",
        description="固定为 bullish，标识这是一份多头观点报告"
    )
    
    # 2. 核心结论
    summary: str = Field(
        min_length=50, max_length=300,
        description="整体看涨观点的精华摘要，200字以内，供研究经理快速了解"
    )
    
    core_thesis: str = Field(
        min_length=100, max_length=500,
        description="核心逻辑链，详细阐述为什么看涨，包含因果关系推理"
    )
    
    # 3. 支撑论据（核心）
    supporting_arguments: List[SupportingArgument] = Field(
        min_items=3, max_items=10,
        description="支撑论据列表，至少3条，最多10条"
    )
    
    # 4. 客观性的体现
    risk_acknowledgment: str = Field(
        min_length=30, max_length=200,
        description="风险承认，展示分析师的客观性，不回避负面因素"
    )
    
    counter_arguments_addressed: List[str] = Field(
        default_factory=list,
        description="已考虑并回应的反方观点列表"
    )
    
    # 5. 置信度
    confidence: int = Field(
        ge=0, le=100,
        description="对看涨观点的综合置信度，0-100分"
    )
    confidence_breakdown: ConfidenceBreakdown = Field(
        description="置信度的多维分解，便于研究经理评估可信度"
    )
    
    # 6. 关键指标速览
    key_metrics_highlight: Dict[str, float] = Field(
        description="从三个维度提取的关键指标速览，如 {'rsi': 65, 'pe': 12.5, 'sentiment': 65}"
    )
    
    # 7. 推理过程摘要
    reasoning_trace: List[str] = Field(
        default_factory=list,
        description="简要的推理过程记录，每轮一句，便于审计"
    )
```
上述仅供参考，实际实现中可能需要根据具体需求进行调整。
## state参数解析
### 输入参数
```python
workflow_id: str
ts_code: str
symbol: str
technical_report: Dict[str, Any] = field(default_factory=dict)
fundamental_report: Dict[str, Any] = field(default_factory=dict)
sentiment_report: Dict[str, Any] = field(default_factory=dict)
technical_score: float = 0.0
fundamental_score: float = 0.0
sentiment_score: float = 0.0 
```
字段	类型	业务含义	对后续节点/系统的作用
workflow_id	str	工作流唯一标识	贯穿全流程，用于日志关联和状态查询
ts_code	str	Tushare标准股票代码	业务主键：告诉研究经理“分析的是哪只股票”
symbol	str	用户友好的股票代码	用于最终报告展示，让用户读懂
technical_report	Dict	阶段一技术分析师的完整输出报告	推理素材：多头研究员从这份报告中提取看涨信号（如“趋势上涨”、“均线金叉”）
fundamental_report	Dict	阶段一基本面分析师的完整输出报告	推理素材：提取看涨信号（如“估值低估”、“ROE高于行业”）
sentiment_report	Dict	阶段一舆情分析师的完整输出报告	推理素材：提取看涨信号（如“舆情积极”、“财报超预期”）
technical_score	float	技术面综合得分（0-100）	参考值：帮助多头判断技术面的量化强度，但最终论据不依赖单一分数
fundamental_score	float	基本面综合得分（0-100）	参考值：同上
sentiment_score	float	舆情综合得分（0-100）	参考值：同上
#### ReAct循环状态
```python
reasoning_round: int = 0
max_rounds: int = 6
is_complete: bool = False
exit_reason: Optional[str] = None
```
字段	取值范围	业务含义	对后续节点/系统的作用
reasoning_round	0 → N	当前已执行的推理轮次，每完成一轮Think→Act→Observe后+1	循环控制：让引擎知道当前是第几轮，防止无限循环
max_rounds	固定6	最大允许的推理轮次上限	安全阀：即使LLM一直不退出，到第6轮也强制停止，保护系统资源
is_complete	True/False	推理是否已完成	流程控制：研究经理在读取多头报告前，先检查此字段，确保多头已完成推理
exit_reason	max_rounds/confidence_high/evidence_sufficient/llm_finish	记录因何原因退出循环	可观测性：让开发者知道Agent是正常完成还是被强制截断，便于调试优化
#### 思考链记录
```python
thought_history: List[Dict[str, Any]] = field(default_factory=list)
# [
#   {"round": 1, "thought": "技术面MA5上穿MA20形成金叉...", "action": "read_technical_report", ...}
# ]
```
字段	业务含义	对后续节点/系统的作用
thought_history	记录ReAct循环中每一轮的完整“思考→行动→观察”过程	可审计性：研究经理可追溯多头的推理过程，判断其逻辑是否合理；开发者可调试Agent的思考路径
#### 证据记录
```python
evidence_collected: List[Dict[str, Any]] = field(default_factory=list)
# {"source": "technical", "point": "MA5上穿MA20形成金叉", "weight": 8, "quote": "..."}
```
字段	业务含义	对后续节点/系统的作用
evidence_collected	多头从三份报告中提取的所有看涨证据，每条标注来源、权重和原始引用	研究经理的核心输入：研究经理会逐条审阅这些证据，判断其质量和说服力；weight字段帮助研究经理快速识别最重要的论据
#### 逻辑链构建
```python
logical_chain: List[str] = field(default_factory=list)
# ["核心逻辑：公司基本面稳健且估值合理...", "支撑逻辑1：均线多头排列..."]
identified_gaps: List[str] = field(default_factory=list)
# ["缺乏近期机构调研数据"]
counter_arguments: List[str] = field(default_factory=list)
# ["大股东减持可能带来短期压力"]
```
字段	业务含义	对后续节点/系统的作用
logical_chain	将证据组织成有层次的逻辑链，从核心逻辑到支撑逻辑	研究经理评估推理深度：逻辑链越长越完整，说明多头的推理越深入，研究报告质量越高
identified_gaps	多头自己识别出的论据不足或数据缺失之处	体现客观性：研究经理会据此判断多头的诚实度，也会在最终报告中标注“数据局限性”
counter_arguments	多头主动考虑的反方观点（自我反驳）	体现严谨性：研究经理会检查多头是否片面看多，处理反方观点的程度影响置信度
#### 置信度评估
```python
confidence: float = 0.0
confidence_factors: Dict[str, float] = field(default_factory=dict)
# {"evidence_quality": 80, "reasoning_depth": 75, "counter_addressed": 60, "multi_dimension_consistency": 85}
```
字段	业务含义	对后续节点/系统的作用
confidence	综合置信度（0-100），多头对“看涨结论”的信心程度	研究经理的加权输入：研究经理在做最终裁决时，会结合多头的置信度来调整综合评分
confidence_factors.evidence_quality	证据质量评分（数据是否充分、来源是否可靠）	研究经理可针对性质疑：“你说证据质量80分，但缺乏机构调研数据，是否应下调？”
confidence_factors.reasoning_depth	逻辑深度评分（推理是否深入、有无因果链）	反映多头分析的质量，研究经理据此判断报告的可信度
confidence_factors.counter_addressed	反方观点处理程度（是否认真考虑了看跌因素）	体现多头的客观性，得分低说明可能过于片面
confidence_factors.multi_dimension_consistency	多维度一致性（技术/基本面/舆情是否指向同一方向）	三方面共振则得分高，信号矛盾则得分低，研究经理据此判断风险是否合理
#### 多头观点报告
```python
bull_report: Optional[Dict[str, Any]] = field(default_factory=dict)
```
字段	业务含义	对后续节点/系统的作用
bull_report	多头研究员的最终输出报告，包含摘要、核心逻辑、支撑论据、置信度等完整内容	研究经理的直接输入：研究经理阅读此报告，结合空头报告，做出最终裁决
bull_report 内部结构已在之前的结构化输出设计中详细定义，包含：

子字段	对研究经理的作用
summary	快速了解多头核心观点
core_thesis	理解多头完整的逻辑链条
supporting_arguments	逐条审阅论据质量
risk_acknowledgment	看多头是否诚实地承认了风险
counter_arguments_addressed	看多头是否考虑了反方观点
confidence	作为裁决的参考权重
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
node_execution_status	记录各执行阶段的状态（success/failed）	流程控制：研究经理启动前检查此字段，若evidence_extraction失败则无法继续
error_message	具体的错误信息	调试：持久化后可追溯失败原因
started_at / completed_at	起止时间	性能监控：记录多头ReAct循环耗时
execution_duration_ms	总执行耗时	成本/性能分析：ReAct循环通常较慢，便于评估是否需要优化提示词或减少轮次
total_tokens_used	LLM调用的Token消耗总量	成本监控：多头Agent是LLM密集型的，便于控制预算