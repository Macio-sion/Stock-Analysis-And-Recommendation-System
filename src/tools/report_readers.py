"""读取三份报告的工具（闭包工厂）。"""
import json

from langchain_core.tools import tool


def make_report_readers(technical_report: dict, fundamental_report: dict, sentiment_report: dict) -> dict:
    """构造读取三份报告的闭包工具，返回 {名称: Tool}。"""

    @tool
    def read_technical_report() -> str:
        """读取技术分析报告，获取趋势方向、关键价位、技术评分。"""
        return json.dumps(technical_report, ensure_ascii=False)

    @tool
    def read_fundamental_report() -> str:
        """读取基本面分析报告，获取估值状态、财务评分、核心指标。"""
        return json.dumps(fundamental_report, ensure_ascii=False)

    @tool
    def read_sentiment_report() -> str:
        """读取舆情分析报告，获取情绪倾向、热度评分、关键事件。"""
        return json.dumps(sentiment_report, ensure_ascii=False)

    return {
        "read_technical_report": read_technical_report,
        "read_fundamental_report": read_fundamental_report,
        "read_sentiment_report": read_sentiment_report,
    }
