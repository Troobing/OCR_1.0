"""
下载路由 — POST /api/download
负责：生成 Word 文档并保存到磁盘
Config: 无（下载目录由 file_utils.get_download_dir 提供）
（网页端的 Word 下载功能）
Skill：文件写入、unique_path 自动编号避重名
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import DownloadRequest
from app.services.word_generator import generate_word
from app.utils.file_utils import get_download_dir, unique_path

router = APIRouter(tags=["下载"])


@router.post("/download")
async def download_word(request: DownloadRequest):
    """生成 Word 文档，存到磁盘，返回文件路径"""
    if not request.image_ids or not request.contents:
        raise HTTPException(status_code=400, detail="请提供图片 ID 和提取内容")
    if len(request.image_ids) != len(request.contents):
        raise HTTPException(status_code=400, detail="image_ids 和 contents 数量不匹配")
    if not any(c.strip() for c in request.contents):
        raise HTTPException(status_code=400, detail="提取内容为空，请先进行提取操作")

    try:
        file_bytes, filename, _ = generate_word(
            contents=request.contents, image_ids=request.image_ids, merge=request.merge,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成 Word 文档失败：{str(e)}")

    filepath = unique_path(get_download_dir() / filename)
    filepath.write_bytes(file_bytes)
    return {"path": str(filepath), "filename": filepath.name}
