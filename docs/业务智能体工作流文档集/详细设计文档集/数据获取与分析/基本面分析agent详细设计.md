# 基面面分析agent详细设计
## 数据源示例
```python
# 导入tushare
import tushare as ts
# 初始化pro接口
pro = ts.pro_api('9ecb767ab40b5023b62abd2ac9a272c93e9bf6f4c9a7bbdf51e22163')
# 拉取数据
df = pro.fina_indicator(**{
    "ts_code": "600000.SH",
    "ann_date": "",
    "start_date": "",
    "end_date": "",
    "period": "",
    "update_flag": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "ann_date",
    "end_date",
    "eps",
    "dt_eps",
    "total_revenue_ps",
    "revenue_ps",
    "capital_rese_ps",
    "surplus_rese_ps",
    "undist_profit_ps",
    "extra_item",
    "profit_dedt",
    "gross_margin",
    "current_ratio",
    "quick_ratio",
    "cash_ratio",
    "ar_turn",
    "ca_turn",
    "fa_turn",
    "assets_turn",
    "op_income",
    "ebit",
    "ebitda",
    "fcff",
    "fcfe",
    "current_exint",
    "noncurrent_exint",
    "interestdebt",
    "netdebt",
    "tangible_asset",
    "working_capital",
    "networking_capital",
    "invest_capital",
    "retained_earnings",
    "diluted2_eps",
    "bps",
    "ocfps",
    "retainedps",
    "cfps",
    "ebit_ps",
    "fcff_ps",
    "fcfe_ps",
    "netprofit_margin",
    "grossprofit_margin",
    "cogs_of_sales",
    "expense_of_sales",
    "profit_to_gr",
    "saleexp_to_gr",
    "adminexp_of_gr",
    "finaexp_of_gr",
    "impai_ttm",
    "gc_of_gr",
    "op_of_gr",
    "ebit_of_gr",
    "roe",
    "roe_waa",
    "roe_dt",
    "roa",
    "npta",
    "roic",
    "roe_yearly",
    "roa2_yearly",
    "debt_to_assets",
    "assets_to_eqt",
    "dp_assets_to_eqt",
    "ca_to_assets",
    "nca_to_assets",
    "tbassets_to_totalassets",
    "int_to_talcap",
    "eqt_to_talcapital",
    "currentdebt_to_debt",
    "longdeb_to_debt",
    "ocf_to_shortdebt",
    "debt_to_eqt",
    "eqt_to_debt",
    "eqt_to_interestdebt",
    "tangibleasset_to_debt",
    "tangasset_to_intdebt",
    "tangibleasset_to_netdebt",
    "ocf_to_debt",
    "turn_days",
    "roa_yearly",
    "roa_dp",
    "fixed_assets",
    "profit_to_op",
    "q_saleexp_to_gr",
    "q_gc_to_gr",
    "q_roe",
    "q_dt_roe",
    "q_npta",
    "q_ocf_to_sales",
    "basic_eps_yoy",
    "dt_eps_yoy",
    "cfps_yoy",
    "op_yoy",
    "ebt_yoy",
    "netprofit_yoy",
    "dt_netprofit_yoy",
    "ocf_yoy",
    "roe_yoy",
    "bps_yoy",
    "assets_yoy",
    "eqt_yoy",
    "tr_yoy",
    "or_yoy",
    "q_sales_yoy",
    "q_op_qoq",
    "equity_yoy"
])
```
以上仅为示例数据，真实数据见项目配置
field字段的指定根据本系统实际业务需求，选择需要的字段。
## agent状态参数示例
### 输入状态
```python
    # 输入状态
    ts_code: str # TS股票代码,e.g. 600001.SH/000001.SZ
    ann_date: str # 日期格式为YYYYMMDD
    start_date: str # 日期格式为YYYYMMDD
    end_date: str # 日期格式为YYYYMMDD
    period: str # 报告期(每个季度最后一天的日期,比如20171231表示年报)
```
字段	类型	业务含义	对后续节点/系统的作用
ts_code	str	股票代码，如 "000001"	全局标识符：用于最终报告展示给用户看，也是整个工作流的业务主键
ann_date	str	公告日期	指定公告日期，用于查询该日期的财报数据
period	str	报告期(每个季度最后一天的日期,比如20171231表示年报)	查询控制：传入 fina_indicator 接口的 period 或 end_date 参数，决定分析哪一期财报
start_date	str	开始日期	查询控制：传入 fina_indicator 接口的 start_date 参数，决定查询哪一期财报数据
end_date	str	结束日期	查询控制：传入 fina_indicator 接口的 end_date 参数，决定查询哪一期财报数据
### 中间状态
#### T1节点数据
```python
financial_raw: Optional[Dict[str, Any]] = field(default_factory=dict)
# {"roe": 15.2, "net_profit_margin": 12.3, "gross_margin": 35.6, ...}
valuation_raw: Optional[Dict[str, Any]] = field(default_factory=dict)
# {"pe": 12.5, "pb": 1.8, "ps": 2.1, ...}
```
字段	业务含义（示例值）	对后续节点/系统的作用
financial_raw	财务核心指标：包含ROE（净资产收益率）、净利率、毛利率等。	数据源：为“节点2：维度评分”提供计算基础，所有的盈利能力、成长能力、财务健康评分都源自这里。
valuation_raw	估值与市值数据：包含PE（市盈率）、PB（市净率）、PS（市销率）等。	数据源：为“节点3：估值判断”提供原始数据，用于计算估值分位数、对比行业均值等。
#### T2节点数据
```python
dimension_scores: Optional[Dict[str, float]] = field(default_factory=dict)
# {"profit": 75, "growth": 68, "health": 62, "combined": 68.3}
```
字段	业务含义（示例值）	对后续节点/系统的作用
profit	盈利能力评分 (75)：基于ROE、毛利率等计算出的综合得分。	反映了公司的赚钱能力强弱。
growth	成长能力评分 (68)：基于营收/利润增长率计算。	反映了公司的发展潜力。
health	财务健康评分 (62)：基于资产负债率、流动比率等计算。	反映了公司的偿债能力和财务安全性。
combined	综合基本面评分 (68.3)：上述三个维度的加权平均值。	汇总输出：这是基本面分析的核心量化结论，会传递给“阶段二：研究经理Agent”和“阶段三：策略执行agent”，作为综合评分的重要组成部分。
#### T3节点数据
```python
valuation: Optional[Dict[str, Any]] = field(default_factory=dict)
# {
#   "status": "低估",
#   "pe": 12.5,
#   "pe_percentile": 25,
#   "pb": 1.8,
#   "industry_pe_avg": 18.5,
#   "valuation_gap": -32.4
# }
```
字段	业务含义（示例值）	对后续节点/系统的作用
status	估值状态：低估	核心结论：直接告诉下游该股票是“低估/合理/高估”，是阶段二“多空辩论”和阶段三“策略执行”的核心依据之一。
pe	当前市盈率：12.5	基础数据，用于计算分位数和偏离度。
pe_percentile	历史分位数：25%	判断当前PE在历史中处于什么位置（25%表示比历史上75%的时间都便宜）。
pb	当前市净率：1.8	另一个核心估值指标，辅助判断。
industry_pe_avg	行业平均市盈率：18.5	对比基准：用于判断个股相对行业是贵还是便宜，是决定status的参考依据。
valuation_gap	偏离度：-32.4%	直观量化了个股与行业均值的差距，可用于生成报告中的建议。
#### T4节点数据
```python
fundamental_score: Optional[float] = None
fundamental_report: Optional[Dict[str, Any]] = field(default_factory=dict)
```
字段	业务含义（示例值）	对后续节点/系统的作用
fundamental_score	基本面综合得分：68	量化输入：作为“技术/基本面/舆情”三维度得分之一，直接输入给阶段二和阶段三。它比 dimension_scores.combined 更综合，可能还考虑了估值因素。
report	完整的分析报告	可读性输出：供下游节点（如研究经理）生成最终推荐理由时引用，也为系统提供可追溯的分析过程。

fundamental_report 内部字段详解：
字段	业务含义（示例值）	对后续节点/系统的作用
score	综合得分：68	与 fundamental_score 冗余，保持报告的自包含性。
valuation_status	估值状态：低估	来自 valuation.status，报告中的关键结论。
summary	文本摘要：“公司ROE高于行业平均，但负债率略高，当前估值偏低...”	直接引用：供阶段二的“研究经理”或阶段三的“推荐决策器”直接拼入最终的推荐理由中，使输出更自然。
metrics	关键指标速览：{"roe": 15.2, "pe": 12.5, ...}	数据快照：便于下游或前端快速展示关键数据。
strengths	优势列表：["盈利能力稳定", "估值具有安全边际"]	决策依据：供多头研究员作为看涨论据。
risks	风险列表：["资产负债率偏高"]	决策依据：供空头研究员作为看跌论据。
### 运行元数据
```python
node_execution_status: Dict[str, str] = field(default_factory=dict)
error_message: Optional[str] = None
started_at: Optional[datetime] = None
completed_at: Optional[datetime] = None
execution_duration_ms: Optional[int] = None
```
字段	业务含义	对后续节点/系统的作用
node_execution_status	记录每个节点的执行状态，如 {"data_fetch": "success"}。	流程控制：用于判断某个步骤是否成功，支持重试或错误处理逻辑。
error_message	记录具体的错误信息。	调试与日志：当某个节点执行失败时，记录原因，便于排查。
started_at / completed_at	记录Agent运行的起止时间。	性能监控：用于计算 execution_duration_ms。
execution_duration_ms	记录该Agent总执行耗时（毫秒）。	性能优化：便于发现性能瓶颈（如某次调用Tushare特别慢）。