# 策略执行agent详细设计
## 数据源示例
### 综合分析报告输入（来自研究经理）
```python
comprehensive_report = {
    "rating": "看多",
    "summary": "基本面稳健且估值合理，技术面确认突破...",
    "comprehensive_score": 72,
    "score_breakdown": {"technical": 72, "fundamental": 68, "sentiment": 65, "debate_adjust": 5},
    "core_drivers": ["ROE高于行业", "均线多头排列"],
    "main_risks": ["资产负债率偏高"]
}
```
### 策略配置输入（用户/默认）
```python
strategy_config = {
    "strategy_type": "价值型",   # 价值型/成长型/技术型/情绪型/均衡型/自定义
    "weights": {"fundamental": 0.7, "technical": 0.2, "sentiment": 0.1}
}
```
以上为示例数据，真实数据见项目配置。
### 自定义算法描述输入（自定义算法模式下）
```text
用户描述：根据三维度得分加权计算综合评分，基本面 60%、技术 30%、舆情 10%，
评分 >= 70 推荐买入，40-69 观望，< 40 回避。
```
> 注：自定义算法模式下，策略执行切换至「代码生成与沙箱执行引擎」管线，详见其详细设计文档。

## agent状态参数示例
### 输入状态
```python
workflow_id: str
ts_code: str
symbol: str
comprehensive_report: Optional[Dict[str, Any]] = field(default_factory=dict)
strategy_config: Optional[Dict[str, Any]] = field(default_factory=dict)
technical_score: float = 0.0
fundamental_score: float = 0.0
sentiment_score: float = 0.0
```
字段	类型	业务含义	对后续节点/系统的作用
workflow_id	str	工作流唯一标识	贯穿全流程，用于日志关联和状态查询
ts_code	str	Tushare标准股票代码	业务主键：唯一确定推荐标的
symbol	str	用户友好的股票代码	用于最终推荐展示，让用户读懂
comprehensive_report	Dict	研究经理的综合分析报告	核心输入：评分与评级的来源
strategy_config	Dict	用户或默认的策略配置	权重来源：决定各维度的加权比例
technical_score	float	技术面得分（0-100）	加权计算的技术维度输入
fundamental_score	float	基本面得分（0-100）	加权计算的基本面维度输入
sentiment_score	float	舆情得分（0-100）	加权计算的舆情维度输入
### 中间状态
#### T1节点数据（策略匹配）
```python
strategy: Optional[Dict[str, Any]] = field(default_factory=dict)
# {"strategy_type": "价值型", "weights": {"fundamental": 0.7, "technical": 0.2, "sentiment": 0.1}}
```
字段	存储内容	业务含义	对后续节点/系统的作用
strategy.strategy_type	"价值型"等	识别的策略类型	决定权重加载逻辑
strategy.weights	三维度权重字典	各维度的加权比例	节点2加权计算的权重来源
#### T2节点数据（评分计算）
```python
scoring: Optional[Dict[str, Any]] = field(default_factory=dict)
# {"weighted_score": 72.3, "confidence_interval": [65.0, 79.6], "benchmark_diff": 3.2}
```
字段	存储内容	业务含义	对后续节点/系统的作用
weighted_score	72.3	加权综合得分	节点3阈值比较的核心输入
confidence_interval	[65.0, 79.6]	置信区间	反映得分的波动范围，供用户了解结论稳定性
benchmark_diff	3.2	与历史基准的差值	判断相对历史表现，辅助决策
#### T3节点数据（推荐决策）
```python
recommendation: Optional[Dict[str, Any]] = field(default_factory=dict)
# {"action": "买入", "score": 72.3, "confidence": "中", "reasons": [...]}
```
字段	业务含义	对后续节点/系统的作用
action	推荐动作：买入/持有/观望/回避	最终结论，直接面向用户
score	综合得分	支持 action 的量化依据
confidence	置信度	帮助用户理解结论的可靠性
reasons	推荐理由列表	节点4报告生成的素材
#### T4节点数据（报告生成）
```python
final_report: Optional[Dict[str, Any]] = field(default_factory=dict)
# {"action": "买入", "score": 72.3, "rating": "看多", "reasons": "...", "risk_tips": "..."}
```
字段	业务含义	对后续节点/系统的作用
final_report	最终推荐报告	直接返回给用户界面展示
### 运行元数据
```python
node_execution_status: Dict[str, str] = field(default_factory=dict)
error_message: Optional[str] = None
started_at: Optional[datetime] = None
completed_at: Optional[datetime] = None
execution_duration_ms: Optional[int] = None
```
字段	业务含义	对后续节点/系统的作用
node_execution_status	记录每个节点的执行状态	流程控制：用于判断某步骤是否成功，支持重试
error_message	具体错误信息	调试与日志
started_at / completed_at	Agent起止时间	性能监控
execution_duration_ms	总执行耗时	性能优化

## 自定义算法模式
当用户选择「自定义算法」时，本 agent 的默认硬编码管线被跳过，改由「代码生成与沙箱执行引擎」接管：LLM 生成 Python 代码 → AST 静态校验 → Docker 沙箱编译执行 → WebSocket 实时推送日志与指标。

详见文档：[代码生成与沙箱执行引擎详细设计](docs\业务智能体工作流文档集\详细设计文档集\策略执行与推荐生成\代码生成与沙箱执行引擎详细设计.md)
