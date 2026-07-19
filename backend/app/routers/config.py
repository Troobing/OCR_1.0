"""
配置路由 — GET/POST /api/config
负责：把 HTTP 请求转发到 config_service
Config: 无（配置逻辑全部在 services/config_service.py）
（网页端的 API 配置读写接口）
Skill：FastAPI APIRouter
"""

from fastapi import APIRouter

from app.models.schemas import ConfigUpdateRequest
from app.services import config_service

router = APIRouter(tags=["配置"])


@router.get("/config")
async def get_config():
    """返回配置（api_key 为掩码，前端永不接触明文 key）"""
    return config_service.read_config_masked()


@router.post("/config")
async def save_config(data: ConfigUpdateRequest):
    """增量保存配置。api_key 为空时保留原值，避免掩码误覆盖。"""
    config_service.save_config(
        base_url=data.base_url,
        api_key=data.api_key,
        model=data.model,
    )
    return {"status": "ok"}
