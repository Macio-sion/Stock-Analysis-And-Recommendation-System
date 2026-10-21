"""A 股舆情数据客户端（akshare），带 Redis 缓存。

数据源：东方财富个股新闻（通过 akshare 的 stock_news_em 接口）。
"""
import json

import pandas as pd

# 兼容 akshare：pandas 3.x 默认 pyarrow string 后端，其正则不支持 \u 转义，改用 python 后端
pd.set_option("mode.string_storage", "python")

import akshare as ak

from src.data.cache import cache_get, cache_set


def _to_ak_symbol(symbol: str) -> str:
    """ts_code（000001.SZ）→ akshare 6 位数字代码（000001）。"""
    return symbol.split(".")[0]


def fetch_sentiment(symbol: str, start_date: str, end_date: str) -> dict:
    """通过 akshare 获取 A 股个股新闻。

    返回结构（示例）：
    {
      "news_list": [
        {"title": "...", "content": "...", "source": "...", "datetime": "..."}
      ]
    }
    """
    ak_symbol = _to_ak_symbol(symbol)
    cache_key = f"sentiment:{ak_symbol}"
    cached = cache_get(cache_key)
    if cached:
        return json.loads(cached)

    df = ak.stock_news_em(symbol=ak_symbol)
    news_list = []
    for _, row in df.iterrows():
        news_list.append(
            {
                "title": str(row.get("新闻标题", "")),
                "content": str(row.get("新闻内容", "")),
                "source": str(row.get("文章来源", "")),
                "datetime": str(row.get("发布时间", "")),
            }
        )

    data = {"news_list": news_list}
    cache_set(cache_key, json.dumps(data), ttl=3600)
    return data
