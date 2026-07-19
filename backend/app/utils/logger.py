"""
日志工具 — 统一 logger 配置，stdout 输出
负责：模块级 logger 创建、格式化、级别
Config: 日志级别、输出格式
（所有端共用 — 开发与 exe 共用同一套日志）
Skill：logging 标准库
"""

import logging
import sys

_LOGGER_NAME = "ocr_agent"
_CONFIGURED = False


def _ensure_configured() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger(_LOGGER_NAME)
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    root.propagate = False  # 避免被 root logger 重复输出
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """获取 ocr_agent 命名空间下的子 logger。"""
    _ensure_configured()
    if name == _LOGGER_NAME:
        return logging.getLogger(_LOGGER_NAME)
    return logging.getLogger(f"{_LOGGER_NAME}.{name}")
