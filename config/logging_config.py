"""日志配置（loguru）。"""
import sys

from loguru import logger

from config.settings import settings


def setup_logging() -> None:
    """初始化日志，输出到控制台与文件。"""
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    logger.add("logs/app.log", rotation="10 MB", retention="7 days", level=settings.log_level)


__all__ = ["setup_logging", "logger"]
