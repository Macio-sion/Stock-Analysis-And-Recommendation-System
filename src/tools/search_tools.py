"""跨报告搜索工具（闭包工厂）。"""
import json

from langchain_core.tools import tool


def make_search_tool(technical_report: dict, fundamental_report: dict, sentiment_report: dict):
    """构造在报告中按关键词搜索的闭包工具。"""

    @tool
    def search_report(keyword: str) -> str:
        """在分析报告中按关键词搜索相关内容，如 "估值"、"金叉"、"减持"。"""
        results = []
        for name, report in [
            ("technical", technical_report),
            ("fundamental", fundamental_report),
            ("sentiment", sentiment_report),
        ]:
            text = json.dumps(report, ensure_ascii=False)
            if keyword in text:
                results.append(f"[{name}] {text[:500]}")
        return "\n---\n".join(results) if results else f"未找到与 '{keyword}' 相关的内容"

    return search_report
