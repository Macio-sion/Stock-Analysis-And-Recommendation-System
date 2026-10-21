# 策略执行agent概要设计
## 数据源
- 阶段二研究经理输出的综合分析报告（ResearchManagerState.comprehensive_report）
- 用户策略配置或默认策略配置（策略类型与各维度权重）
- 用户自定义算法描述（自定义算法模式下，作为代码生成引擎的输入）

## 策略执行agent结构设计
```mermaid
flowchart TD
    A[输入1: 综合分析报告] --> B[输入2: 用户策略配置]
    A --> C[输入2: 默认策略配置]
    
    B --> D[策略匹配引擎]
    C --> D
    
    subgraph D [策略匹配引擎]
        D1{识别策略类型}
        D1 -->|价值型| D1a[权重: 基本面70%, 技术20%, 舆情10%]
        D1 -->|成长型| D1b[权重: 基本面50%, 技术30%, 舆情20%]
        D1 -->|技术型| D1c[权重: 技术60%, 基本面20%, 舆情20%]
        D1 -->|情绪型| D1d[权重: 舆情50%, 技术30%, 基本面20%]
        D1 -->|均衡型| D1e[权重: 各维度均衡]
        D1 -->|自定义| D1f[按用户指定权重]
    end
    
    D1a --> E[评分计算器]
    D1b --> E
    D1c --> E
    D1d --> E
    D1e --> E
    D1f --> E
    
    subgraph E [评分计算器]
        E1[加权计算综合得分]
        E2[计算置信区间]
        E3[对比历史基准]
    end
    
    E1 --> F[推荐决策器]
    E2 --> F
    E3 --> F
    
    subgraph F [推荐决策器]
        F1{综合得分阈值}
        F1 -->|≥ 70| F1a[推荐: 买入]
        F1 -->|40-69| F1b[推荐: 持有/观望]
        F1 -->|< 40| F1c[推荐: 回避]
    end
    
    F1a --> G[生成推荐理由]
    F1b --> G
    F1c --> G
    
    G --> H[输出: 最终推荐结果]
```
## agent节点设计

节点	节点类型	输入	输出	状态变更
S1: 策略匹配	规则引擎	{comprehensive_report, strategy_config}	{strategy_type, weights}	(state.strategy = {...})
S2: 评分计算	原子操作	strategy	{weighted_score, confidence_interval, benchmark_diff}	state.scoring = {...}
S3: 推荐决策	规则引擎	scoring	{action, score, confidence, reasons}	state.recommendation = {...}
S4: 报告生成	模板填充	recommendation	{final_report}	state.final_report = {...}

节点间连接方式：纯链式（Pipeline）——每个节点的输出是下一个节点的输入，无分支无循环。

## 图状态维护
```python
class StrategyAgentState:
    # 输入参数
    workflow_id: str
    ts_code: str
    symbol: str
    comprehensive_report: Optional[Dict[str, Any]] = field(default_factory=dict)  # 来自研究经理
    strategy_config: Optional[Dict[str, Any]] = field(default_factory=dict)         # 用户/默认策略配置
    # 三维度得分（用于加权计算）
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    sentiment_score: float = 0.0
    # ========== 节点1输出：策略匹配 ==========
    strategy: Optional[Dict[str, Any]] = field(default_factory=dict)
    # {"strategy_type": "价值型", "weights": {"fundamental": 0.7, "technical": 0.2, "sentiment": 0.1}}
    # ========== 节点2输出：评分计算 ==========
    scoring: Optional[Dict[str, Any]] = field(default_factory=dict)
    # {"weighted_score": 72.3, "confidence_interval": [65.0, 79.6], "benchmark_diff": 3.2}
    # ========== 节点3输出：推荐决策 ==========
    recommendation: Optional[Dict[str, Any]] = field(default_factory=dict)
    # {"action": "买入", "score": 72.3, "confidence": "中", "reasons": [...]}
    # ========== 节点4输出：最终报告 ==========
    final_report: Optional[Dict[str, Any]] = field(default_factory=dict)
    # {"action": "买入", "score": 72.3, "rating": "看多", "reasons": "...", "risk_tips": "..."}
    # ========== 执行元数据 ==========
    node_execution_status: Dict[str, str] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_duration_ms: Optional[int] = None
```

## 自定义算法模式
当用户选择「自定义算法」时，策略执行不走本 agent 的默认硬编码管线，而是切换到「代码生成与沙箱执行引擎」管线：LLM 生成代码 → AST 校验 → Docker 沙箱编译执行，并实时展示代码、日志与曲线图。

详见文档：[代码生成与沙箱执行引擎概要设计](docs\业务智能体工作流文档集\概要设计文档集\策略执行与推荐生成\代码生成与沙箱执行引擎概要设计.md)
