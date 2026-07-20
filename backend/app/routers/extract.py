"""
提取路由 — POST /api/extract
负责：从 .env 读 API Key → 并发批量调用 LLM → 返回文字和 LaTeX 公式
Config: 错误处理策略
（网页端的 AI 提取功能）
Skill：asyncio.gather + Semaphore、逐图容错
"""

import asyncio

from fastapi import APIRouter, HTTPException

from app.models.schemas import ExtractRequest, ExtractResponse, ExtractResult
from app.settings import get_config
from app.services.llm_client import extract_from_image
from app.utils.constants import MAX_CONCURRENCY
from app.utils.file_utils import get_image_bytes
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["提取"])


@router.post("/extract", response_model=ExtractResponse)
async def extract_content(request: ExtractRequest):
    """AI 提取图片中的文字和数学公式。API Key 从 .env 读取。"""
    if not request.image_ids:
        raise HTTPException(status_code=400, detail="请至少指定一张图片")

    cfg = get_config()
    if not cfg["api_key"]:
        raise HTTPException(
            status_code=400,
            detail="未配置 API Key，请在 .env 文件中设置 LLM_API_KEY",
        )

    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async def _extract_one(image_id: str) -> ExtractResult:
        async with semaphore:
            try:
                image_data, mime_type = get_image_bytes(image_id)
                content = await extract_from_image(
                    image_data=image_data, mime_type=mime_type,
                    api_key=cfg["api_key"], base_url=cfg["base_url"], model=cfg["model"],
                )
                return ExtractResult(
                    image_id=image_id, filename=image_id,
                    content=content, status="success", error=None,
                )
            except FileNotFoundError:
                return ExtractResult(
                    image_id=image_id, filename="未知", content="",
                    status="error", error="图片不存在，请重新上传",
                )
            except ValueError as e:
                return ExtractResult(
                    image_id=image_id, filename="未知",
                    content="", status="error", error=str(e),
                )
            except Exception as e:
                logger.exception("提取图片 %s 失败", image_id)
                return ExtractResult(
                    image_id=image_id, filename="未知",
                    content="", status="error", error=f"调用 AI 失败：{str(e)}",
                )

    results = await asyncio.gather(*[_extract_one(iid) for iid in request.image_ids])
    return ExtractResponse(results=list(results))
