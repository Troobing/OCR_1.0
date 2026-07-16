"""
下载路由 — POST /api/download
接收提取内容 → 调用 word_generator 生成 .docx → StreamingResponse 返回文件下载
Config: 下载文件名、单文件/zip 逻辑、Content-Disposition 头
"""

import io
from urllib.parse import quote
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import DownloadRequest
from app.services.word_generator import generate_word

router = APIRouter(tags=["下载"])


@router.post("/download")
async def download_word(request: DownloadRequest):
    """生成 Word 文档并触发浏览器下载"""
    if not request.image_ids or not request.contents:
        raise HTTPException(status_code=400, detail="请提供图片 ID 和提取内容")
    if len(request.image_ids) != len(request.contents):
        raise HTTPException(status_code=400, detail="image_ids 和 contents 数量不匹配")
    if not any(c.strip() for c in request.contents):
        raise HTTPException(status_code=400, detail="提取内容为空，请先进行提取操作")

    try:
        file_bytes, filename, mime_type = generate_word(
            contents=request.contents,
            image_ids=request.image_ids,
            merge=request.merge,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成 Word 文档失败：{str(e)}")

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename, safe='')}"
        },
    )
