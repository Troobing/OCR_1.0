"""
提取路由 — POST /api/extract
接收图片 ID 列表 + LLM 配置 → 逐张调用 LLM API → 返回文字和 LaTeX 公式
Config: 并发控制、错误处理策略
（AI 提取 + 自我校验 API）
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import ExtractRequest, ExtractResponse, ExtractResult
from app.services.llm_client import extract_from_image
from app.utils.file_utils import get_image_bytes

router = APIRouter(tags=["提取"])


@router.post("/extract", response_model=ExtractResponse)
async def extract_content(request: ExtractRequest):
    """AI 提取图片中的文字和数学公式"""
    if not request.image_ids:
        raise HTTPException(status_code=400, detail="请至少指定一张图片")

    api_key = request.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key 不能为空，请在前端设置")
    base_url = request.base_url or "https://api.uniapi.io/v1"
    model = request.model or "gpt-4o"

    results = []
    for image_id in request.image_ids:
        try:
            image_data, mime_type = get_image_bytes(image_id)

            content = await extract_from_image(
                image_data=image_data, mime_type=mime_type,
                api_key=api_key, base_url=base_url, model=model,
            )

            results.append(ExtractResult(
                image_id=image_id, filename=image_id,
                content=content, status="success", error=None,
            ))

        except FileNotFoundError:
            results.append(ExtractResult(
                image_id=image_id, filename="未知", content="",
                status="error", error="图片不存在，请重新上传",
            ))
        except ValueError as e:
            results.append(ExtractResult(
                image_id=image_id, filename="未知",
                content="", status="error", error=str(e),
            ))
        except Exception as e:
            results.append(ExtractResult(
                image_id=image_id, filename="未知",
                content="", status="error", error=f"调用 AI 失败：{str(e)}",
            ))

    return ExtractResponse(results=results)
