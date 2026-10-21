"""Tushare 数据客户端（行情 + 财务），带 Redis 缓存。"""
import io

import pandas as pd
import tushare as ts

from config.settings import settings
from src.data.cache import cache_get, cache_set


class TushareClient:
    """封装 Tushare Pro 接口，统一 token 与缓存。"""

    def __init__(self, token: str | None = None):
        self.token = token or settings.tushare_token
        self._pro = None

    @property
    def pro(self):
        if self._pro is None:
            if not self.token:
                raise ValueError("TUSHARE_TOKEN 未配置，请在 .env 中设置")
            self._pro = ts.pro_api(self.token)
        return self._pro

    def get_daily(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取日线行情（OHLCV）。日期格式 YYYYMMDD。"""
        cache_key = f"quote:{ts_code}:{start_date}:{end_date}"
        cached = cache_get(cache_key)
        if cached:
            return pd.read_json(io.StringIO(cached))

        df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        df = df.sort_values("trade_date").reset_index(drop=True)
        cache_set(cache_key, df.to_json(), ttl=3600)
        return df

    def get_fina_indicator(self, ts_code: str, period: str | None = None) -> pd.DataFrame:
        """获取财务指标。period 为报告期（如 20251231），不传则取最新。"""
        cache_key = f"fina:{ts_code}:{period or 'latest'}"
        cached = cache_get(cache_key)
        if cached:
            return pd.read_json(io.StringIO(cached))

        df = self.pro.fina_indicator(ts_code=ts_code, period=period)
        cache_set(cache_key, df.to_json(), ttl=86400)
        return df

    def get_daily_basic(self, ts_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取每日指标（pe/pb/ps 等估值）。"""
        cache_key = f"basic:{ts_code}:{start_date}:{end_date}"
        cached = cache_get(cache_key)
        if cached:
            return pd.read_json(io.StringIO(cached))
        df = self.pro.daily_basic(ts_code=ts_code, start_date=start_date, end_date=end_date)
        cache_set(cache_key, df.to_json(), ttl=3600)
        return df


client = TushareClient()
