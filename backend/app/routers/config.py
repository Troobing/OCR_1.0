"""
配置持久化 — 桌面模式下 localStorage 不持久，存到 config.json 磁盘文件
"""

import json
import sys
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(tags=["配置"])

# 配置文件位置：exe 同目录 或 开发时在 backend/
if getattr(sys, "frozen", False):
    CONFIG_FILE = Path(sys.executable).parent / "config.json"
else:
    CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config.json"

DEFAULTS = {"base_url": "https://api.uniapi.io/v1", "api_key": "", "model": "gpt-4o"}


def _read_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULTS)


@router.get("/config")
async def get_config():
    return _read_config()


@router.post("/config")
async def save_config(data: dict):
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok"}
