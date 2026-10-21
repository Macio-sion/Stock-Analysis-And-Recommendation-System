# 舆情数据分析agent详细设计
## 数据获取示例
```python
import akshare as ak

# 通过 akshare 获取 A 股个股新闻（东方财富）
df = ak.stock_news_em(symbol="000001")  # 平安银行
# 返回字段：关键词、新闻标题、新闻内容、发布时间、文章来源、新闻链接
```
> 注：结果写入 Redis 缓存（TTL）。新闻无现成情感标签，由舆情分析师做关键词情感分析。
## agent状态参数示例
### 输入状态
```python
start_date: str
end_date: str
src: str
```
字段	类型	业务含义	对后续节点/系统的作用
start_date	str	舆情数据采集的起始日期，格式 "YYYY-MM-DD HH:MM:SS"	时间窗口起点，控制采集哪些时间段发布的新闻
end_date	str	舆情数据采集的结束日期	时间窗口终点：确保采集到指定时间范围内的舆情，与 start_date 共同定义分析周期
src	str	数据来源，如 "新浪财经"、"财联社"、"华尔街见闻" 等	数据源控制：指定从哪个/哪些新闻源采集数据.
### 中间状态
#### T1节点数据
```python
social_raw: Optional[Dict[str, Any]] = field(default_factory=dict)
# {
#   "news_list": [{"title": "...", "content": "...", "src": "...", "datetime": "..."}],
#   "social_posts": [{"text": "...", "platform": "...", "interaction_count": 123}]
# }
news_count: Optional[int] = None
posts_count: Optional[int] = None
```
字段	存储内容	业务含义	对后续节点/系统的作用
social_raw.news_list	新闻列表，每条包含标题、正文、来源、发布时间	从新闻API采集到的原始财经新闻，未经任何NLP处理	节点2（NLP分析）的输入：对标题和正文进行情感分析和实体识别
social_raw.social_posts	社交媒体帖子列表，包含文本、平台、互动量	从社交媒体（如股吧、微博）采集的原始用户讨论（如数据源不支持可留空）	节点2（NLP分析）的输入：对帖子文本进行情感分析，判断散户情绪
news_count	整数，如 45	采集到的新闻总条数	数据质量校验：如果新闻数太少（如 < 3），舆情分析结论可信度降低，可在报告中提示
posts_count	整数，如 120	采集到的社交媒体帖子总条数	数据质量校验：作用同上，帮助下游判断结论的统计显著性
#### T2节点数据
```python
nlp_results: Optional[Dict[str, Any]] = field(default_factory=dict)
# {
#   "sentiments": [
#     {"text": "...", "sentiment": "positive", "score": 0.85},
#   ],
#   "entities": ["公司A", "政策B", "产品C"],
#   "topics": {"业绩": 3, "政策": 2, "行业": 1}
# }
```
字段	子字段	业务含义	对后续节点的作用
sentiments	sentiment	每条新闻/帖子的情感分类："positive"（积极）/ "negative"（消极）/ "neutral"（中性）	节点3（情绪量化）的核心输入：统计情感分布，计算综合情绪得分
score	情感强度得分，0-1之间，越接近1表示情绪越强烈	
entities	["公司A", "政策B"]	命名实体识别结果，提取出新闻中提到的公司名、人名、政策名等	事件识别：用于生成 sentiment_report.key_events，如识别出"大股东减持"实体则标记为风险事件
topics	{"业绩": 3, "政策": 2}	主题分类，统计各类话题出现的频次	热点识别：频次最高的主题 → 生成 sentiment_report.hot_topics，供研究经理判断当前市场关注的焦点话题
#### T3节点数据
```python
sentiment: Optional[Dict[str, Any]] = field(default_factory=dict)
# {
#   "sentiment_score": 65.0,           # 0-100
#   "sentiment_distribution": {"positive": 45, "neutral": 35, "negative": 20},
#   "heat_score": 72.0,                # 0-100 热度
#   "polarity": "积极"                  # 积极/中性/消极
# }
```
字段	取值范围	业务含义	对后续节点的作用
sentiment_score	0-100	综合情绪得分：基于所有文本的情感得分加权计算，大于50为偏积极	量化决策依据：作为舆情维度的核心得分，与 technical_score、fundamental_score 并列传入策略引擎
sentiment_distribution	百分比之和=100	情感分布：积极/中性/消极三类文本的占比	判断情绪结构：即便综合得分中性，若极端情绪占比高（如积极和消极都超过40%），说明市场分歧大，研究经理可据此下调置信度
heat_score	0-100	热度得分：基于新闻数量、发帖量、互动量等计算的关注度指标	判断关注度：得分高说明市场正在热议该股票，信息已充分反映在股价中；得分低可能存在信息差
polarity	"积极" / "中性" / "消极"	情绪定性结论：基于 sentiment_score 的定性映射	报告引用：供 sentiment_report.polarity 直接使用，为最终推荐理由提供文本素材
#### T4节点数据
```python
sentiment_score: Optional[float] = None
sentiment_report: Optional[Dict[str, Any]] = field(default_factory=dict)
# {
#   "score": 65,
#   "polarity": "积极",
#   "summary": "近期舆情整体积极，财报利好引发市场关注，但需注意大股东减持传闻...",
#   "key_events": ["公司发布超预期财报", "行业政策利好", "大股东减持"],
#   "hot_topics": ["业绩增长", "政策支持"],
#   "risk_factors": ["减持传闻"]
# }
```
字段	业务含义	对后续节点/系统的作用
sentiment_score	舆情综合得分（65分），直接复制 sentiment.sentiment_score	阶段三策略引擎的核心输入：与 technical_score、fundamental_score 一起加权计算最终推荐得分
report.score	冗余存储，保持报告自包含性	供研究经理直接引用，无需额外查询
report.polarity	情绪定性结论（来自 sentiment.polarity）	报告核心结论，供阶段二多头/空头研究员引用
report.summary	文本摘要："近期舆情整体积极，财报利好引发市场关注，但需注意大股东减持传闻..."	直接拼入最终推荐理由：阶段三 reasoning 会直接拼接此段，让用户了解舆情层面的逻辑
report.key_events	关键事件列表：["公司发布超预期财报", "行业政策利好", "大股东减持"]	多头/空头论据来源：积极事件（如"超预期财报"）→ 多头引用；消极事件（如"大股东减持"）→ 空头引用
report.hot_topics	热点话题列表：["业绩增长", "政策支持"]	反映市场当前关注的焦点，研究经理可据此判断是否存在"过度炒作"或"被忽视的价值"
report.risk_factors	风险因素列表：["减持传闻"]	空头研究员/风险管理的重要输入：直接作为看跌论据或风险提示
### 元数据
```python
node_execution_status: Dict[str, str] = field(default_factory=dict)
error_message: Optional[str] = None
started_at: Optional[datetime] = None
completed_at: Optional[datetime] = None
execution_duration_ms: Optional[int] = None
```
字段	业务含义	对后续节点/系统的作用
node_execution_status	记录每个节点的执行状态，如 {"data_fetch": "success", "nlp_analysis": "success"}	流程控制：判断从哪个节点恢复（如 nlp_analysis 失败则重试）
error_message	具体错误信息，如 "舆情API调用超时"	调试与告警：持久化后运维可查询失败原因
started_at / completed_at	该Agent的起止时间	性能监控：舆情API通常较慢，便于评估耗时是否在可接受范围
execution_duration_ms	该Agent总执行耗时（毫秒）	成本/性能分析：如耗时过长可考虑减少采集条数或增加缓存，以优化效率