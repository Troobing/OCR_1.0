"""
项目级常量 — 跨模块共享
Config: MAX_CONCURRENCY
"""

# 批量提取 LLM 并发上限（bridge.py 与 extract.py 共用）
MAX_CONCURRENCY = 5
