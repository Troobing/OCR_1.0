"""
配置路由 — POST /api/config, GET /api/config
前端 API 设置 ↔ 后端内存同步桥梁，extract 接口的 fallback 默认值来源
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["配置"])

_backend_config: dict = {
    "base_url": "https://api.uniapi.io/v1",
    "api_key": "",
    "model": "gpt-4o",
}


class ConfigData(BaseModel):
    base_url: str
    api_key: str
    model: str


def get_backend_config() -> dict:
    """供 extract 等接口读取后端当前保存的配置"""
    return dict(_backend_config)


@router.post("/config")
async def save_config(config: ConfigData):
    """前端保存 API 设置时同步到后端内存"""
    _backend_config.update(config.model_dump())
    return {"status": "ok", "message": "配置已同步到后端"}


@router.get("/config")
async def get_config():
    """返回后端当前配置"""
    key = _backend_config["api_key"]
    return {
        "base_url": _backend_config["base_url"],
        "api_key": key,
        "api_key_masked": (key[:8] + "****" + key[-4:]) if len(key) > 12 else "未设置",
        "model": _backend_config["model"],
    }
