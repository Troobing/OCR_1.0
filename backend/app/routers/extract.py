"""
提取路由 — POST /api/extract
接收图片 ID 列表 + LLM 配置 → 逐张调用 LLM API → 返回提取的文字和 LaTeX 公式
Config: 并发控制、错误处理策略、API 配置 fallback 优先级
"""

from fastapi import APIRouter, HTTPException
from app.models.schemas import ExtractRequest, ExtractResponse, ExtractResult
from app.services.llm_client import extract_from_image, verify_extraction
from app.utils.file_utils import get_image_path
from app.routers.config import get_backend_config

router = APIRouter(tags=["提取"])


@router.post("/extract", response_model=ExtractResponse)
async def extract_content(request: ExtractRequest):
    """AI 提取图片中的文字和数学公式"""
    if not request.image_ids:
        raise HTTPException(status_code=400, detail="请至少指定一张图片")

    # 配置 fallback：优先用请求里的，没有则从后端内存取
    backend_config = get_backend_config()
    base_url = request.base_url or backend_config["base_url"]
    model = request.model or backend_config["model"]
    api_key = (request.api_key or "").strip() or backend_config.get("api_key", "")
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key 不能为空，请在前端设置或请求中提供")

    results = []
    for image_id in request.image_ids:
        try:
            image_path = get_image_path(image_id)
            if not image_path.exists():
                results.append(ExtractResult(
                    image_id=image_id, filename="未知", content="",
                    status="error", error="图片文件不存在，可能已被清理，请重新上传",
                ))
                continue

            content = await extract_from_image(
                image_path=str(image_path),
                api_key=api_key, base_url=base_url, model=model,
            )

            # 自我校验：把首轮结果发回 AI 对照原图修正。失败则用原文
            try:
                verified, _ = await verify_extraction(
                    image_path=str(image_path),
                    extracted_text=content,
                    api_key=api_key, base_url=base_url, model=model,
                )
                content = verified
            except Exception:
                pass  # 校验失败不中断，保留首次提取结果

            results.append(ExtractResult(
                image_id=image_id, filename=image_path.name,
                content=content, status="success", error=None,
            ))

        except ValueError as e:
            results.append(ExtractResult(
                image_id=image_id,
                filename=image_path.name if image_path.exists() else "未知",
                content="", status="error", error=str(e),
            ))
        except Exception as e:
            results.append(ExtractResult(
                image_id=image_id,
                filename=image_path.name if image_path.exists() else "未知",
                content="", status="error", error=f"调用 AI 失败：{str(e)}",
            ))

    return ExtractResponse(results=results)
