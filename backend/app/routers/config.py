"""
配置持久化 — API Key 加密存到 config.json，用本机特征码做密钥
Config: 加密密钥、存储路径、默认值
（桌面模式下保存和读取 API 配置）
Skill：XOR 加密、hashlib、JSON
"""

import hashlib
import base64
import json
import platform
import sys
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(tags=["配置"])

if getattr(sys, "frozen", False):
    CONFIG_FILE = Path(sys.executable).parent / "config.json"
else:
    CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config.json"

DEFAULTS = {"base_url": "https://api.uniapi.io/v1", "api_key": "", "model": "gpt-4o"}

# 用本机特征派生加密密钥——换台机器拷走 config.json 也解不开
_KEY = hashlib.sha256(f"{platform.node()}{platform.machine()}".encode()).digest()


def _encrypt(text: str) -> str:
    if not text:
        return ""
    data = text.encode()
    return base64.b64encode(bytes(a ^ _KEY[i % len(_KEY)] for i, a in enumerate(data))).decode()


def _decrypt(encoded: str) -> str:
    if not encoded:
        return ""
    data = base64.b64decode(encoded)
    return bytes(a ^ _KEY[i % len(_KEY)] for i, a in enumerate(data)).decode()


def _read_config() -> dict:
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        cfg["api_key"] = _decrypt(cfg.get("api_key", ""))
        return cfg
    except Exception:
        return dict(DEFAULTS)


@router.get("/config")
async def get_config():
    return _read_config()


@router.post("/config")
async def save_config(data: dict):
    data["api_key"] = _encrypt(data.get("api_key", ""))
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"status": "ok"}
