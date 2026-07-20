"""
图片删除路由 — DELETE /api/images/{image_id}
负责：前端删图时同步清理后端内存存储
（网页端的图片删除功能）
Skill：FastAPI 路径参数
"""

from fastapi import APIRouter

from app.utils import file_utils

router = APIRouter(tags=["图片"])


@router.delete("/images/{image_id}")
async def delete_image(image_id: str):
    deleted = file_utils.remove_image(image_id)
    return {"deleted": deleted}
