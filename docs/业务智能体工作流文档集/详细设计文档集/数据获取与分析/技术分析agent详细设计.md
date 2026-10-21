# 技术分析agent详细设计
## 数据源示例
```python
# 导入tushare
import tushare as ts
# 初始化pro接口
pro = ts.pro_api('9ecb767ab40b5023b62abd2ac9a272c93e9bf6f4c9a7bbdf51e22163')

# 拉取数据
df = pro.daily(**{"ts_code": "","trade_date": "","start_date": "","end_date": "",
    "limit": "",
    "offset": ""
}, fields=[
    "ts_code",
    "trade_date",
    "open",
    "high",
    "low",
    "close",
    "pre_close",
    "change",
    "pct_chg",
    "vol",
    "amount"
])
```
field字段的指定根据本系统实际业务需求，选择需要的字段。

## agent状态参数示例
### 输入状态
```python
# 输入参数
ts_code: str # Tushare标准股票代码，如 "000001.SZ"
start_date: str # 数据起始日期，格式 YYYYMMDD，如 "20250101"                      
end_date: str # 数据结束日期，格式 YYYYMMDD，如 "20260831"
```
字段	业务含义	对后续节点/系统的作用
ts_code	Tushare标准股票代码，如 000001.SZ。	全局标识符：唯一确定分析标的，所有后续API调用和结果存储都依赖此字段。
start_date	数据获取的起始日期。	用于限定 daily 接口的查询范围，控制获取哪些报告期的股票数据。
end_date	数据获取的结束日期。	与 start_date 共同构成时间窗口，确保获取到最新的可用股票数据。
### 中间状态
#### T1节点数据
```python
# ========== 节点1输出：原始数据 ==========
raw_ohlcv: Optional[pd.DataFrame] = None   # 原始OHLCV数据
data_record_count: Optional[int] = None    # 数据条数
```
字段	存储内容（示例）	业务含义	对后续节点/系统的作用
raw_ohlcv	pd.DataFrame 包含 trade_date, open, high, low, close, vol, amount	原始日线行情数据：直接来自Tushare daily 接口的返回值，未经任何加工	节点2（指标计算）的输入：所有技术指标（MA/MACD/RSI/布林带）都基于这些原始数据计算得出
data_record_count	250（表示250个交易日）	原始数据的数据条数	数据质量校验：如果记录数不足（如少于60条），部分指标无法有效计算，可用于触发降级处理或告警
#### T2节点数据
```python
indicators: Optional[Dict[str, Any]] = field(default_factory=dict)
# {
#   "ma": {"ma5": 12.5, "ma10": 12.3, "ma20": 12.0, "ma60": 11.5},
#   "macd": {"dif": 0.15, "dea": 0.10, "macd": 0.05},
#   "rsi": {"rsi6": 65.2, "rsi12": 58.7, "rsi24": 55.3},
#   "bb": {"upper": 13.2, "middle": 12.0, "lower": 10.8},
#   "vol": {"volume_ratio": 1.2, "obv": 1234567}
# }
```
字段	子字段	取值范围	业务含义	对后续节点的作用
ma	ma5	股价附近	5日均线（最近5个交易日收盘价的平均值）	判断短期趋势：ma5 > ma20 且 ma20 > ma60 表示多头排列（趋势向上），空头研究员可引用相反情况
ma20	股价附近	20日均线（月线），中期趋势参考	
ma60	股价附近	60日均线（季线），长期趋势参考	
macd	dif	正负值	快线（DIF），反映短期与长期均线的差距	判断买卖信号：dif > dea 为金叉（看涨），dif < dea 为死叉（看跌）
dea	正负值	慢线（DEA），DIF的移动平均	
macd	正负值	MACD柱，DIF与DEA的差值	柱体由负转正为买入信号，由正转负为卖出信号
rsi	rsi6	0-100	6日相对强弱指标	判断超买超卖：> 70 为超买（可能回调），< 30 为超卖（可能反弹）
rsi12	0-100	12日相对强弱指标	更平滑的RSI，用于确认趋势
rsi24	0-100	24日相对强弱指标	用于判断中长期动能
bb	upper	股价附近	布林带上轨（中轨 + 2倍标准差）	判断股价位置：股价触及上轨可能超买，触及下轨可能超卖
middle	股价附近	布林带中轨（20日均线）	股价在中轨上方为强势，下方为弱势
lower	股价附近	布林带下轨（中轨 - 2倍标准差）	
vol	volume_ratio	>1 或 <1	量比 = 当日成交量 / 过去5日均量	判断成交量异常：> 1.5 为放量（市场关注度提升），< 0.5 为缩量（交投清淡）
obv	累计值	能量潮（On-Balance Volume），成交量的累计指标	判断量价配合关系，OBV创新高而股价未创新高为看跌背离
#### T3节点数据
```python
trend_analysis: Optional[Dict[str, Any]] = field(default_factory=dict)
# {
#   "trend": "上涨",        # 上涨/下跌/震荡
#   "strength": 72,         # 0-100
#   "key_levels": {"support": 11.8, "resistance": 13.5},
#   "signal_summary": {"buy_signals": 3, "sell_signals": 1, "neutral_signals": 2}
# }
```
字段	业务含义	对后续节点/系统的作用
trend	趋势方向：综合MA排列、MACD方向、RSI位置后的最终判断	核心输出：多头研究员引用 "上涨" 作为看涨论据；空头研究员引用 "下跌" 作为看跌论据
strength	趋势强度：0-100分，基于指标共振程度计算，如多个指标同时看涨则分数高	量化决策依据：阶段三策略引擎可将此作为技术面得分的调整因子
key_levels	关键价位：support（支撑位）是可能止跌反弹的价位；resistance（阻力位）是可能遇阻回落的价位	报告引用：供 technical_report.summary 生成具体描述，如 "下方支撑位11.8元"
signal_summary	信号统计：buy_signals（看涨信号数量）、sell_signals（看跌信号数量）、neutral_signals（中性信号数量）	透明度：让下游了解趋势判断的依据是什么，有多少个指标支持这个结论
#### T4节点数据
```python
technical_score: Optional[float] = None    # 0-100 技术面综合评分
technical_report: Optional[Dict[str, Any]] = field(default_factory=dict)
# {
#   "score": 72,
#   "trend": "上涨",
#   "summary": "短期均线上穿长期均线，RSI处于强势区间...",
#   "key_metrics": {"rsi": 65, "macd_signal": "买入", "bb_position": "中轨上方"},
#   "key_levels": {"support": 11.8, "resistance": 13.5}
# }
```
字段	业务含义	对后续节点/系统的作用
technical_score	技术面综合评分（72分），基于趋势方向、趋势强度、信号数量等综合计算	阶段三策略引擎的核心输入：与 fundamental_score、sentiment_score 一起加权计算最终推荐得分
report.score	冗余存储 technical_score，保持报告的自包含性	供阶段二研究经理直接引用，无需额外查询
report.trend	趋势方向（来自 trend_analysis.trend）	报告中的核心结论，也供阶段二多空双方引用
report.summary	文本摘要："短期均线上穿长期均线，RSI处于强势区间..."	直接拼入最终推荐理由：阶段三 reasoning 字段会直接拼接此段文字
report.key_metrics	关键指标速览：RSI值、MACD信号、布林带位置	供前端展示关键数据、供研究经理快速获取核心指标
report.key_levels	关键价位（支撑/阻力）	供最终报告生成具体的价格参考建议
### 图状态维护
```python
node_execution_status: Dict[str, str] = field(default_factory=dict)
# {"data_fetch": "success", "indicator_calc": "success", "trend_judge": "success", "report_gen": "success"}
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