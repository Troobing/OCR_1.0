"""
项目级常量 — 跨模块共享的配置值
负责：集中管理多处复用的常量，避免散落定义导致不同步
Config: MAX_CONCURRENCY（bridge.py 与 extract.py 共用）
（纯配置，不包含业务逻辑）
"""

# 批量提取 LLM 并发上限（bridge.py 与 extract.py 共用）
MAX_CONCURRENCY = 5
