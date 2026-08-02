"""
日志配置 - 统一管理应用日志
按日轮转，同时输出到文件和控制台
"""
import logging
import sys
from datetime import datetime
from ..config import get_config


_logger: logging.Logger | None = None


def get_logger() -> logging.Logger:
    """获取全局日志器单例"""
    global _logger
    if _logger is not None:
        return _logger

    cfg = get_config()
    log_file = cfg.paths.log_dir / f"canteen_{datetime.now().strftime('%Y%m%d')}.log"

    _logger = logging.getLogger("CanteenApp")
    _logger.setLevel(logging.INFO)
    _logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    return _logger
