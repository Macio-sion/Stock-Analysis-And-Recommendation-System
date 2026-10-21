"""Tushare 连接自检。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.tushare_client import client  # noqa: E402


def main() -> None:
    if not client.token:
        print("TUSHARE_TOKEN 未配置，请在 .env 中设置后重试")
        return
    df = client.get_daily("000001.SZ", "20250101", "20250131")
    print(f"拉取到 {len(df)} 条行情数据")
    print(df.head())
    print("Tushare 连接正常")


if __name__ == "__main__":
    main()
