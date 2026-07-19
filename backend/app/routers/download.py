"""
下载路由 — POST /api/download
负责：生成 Word 文档并保存到磁盘
Config: 下载目录、文件名自动编号规则
（网页端的 Word 下载功能）
Skill：文件写入、自动编号避重名
"""

import sys
from pathlib import Path
from fastapi import APIRouter, HTTPException
from app.models.schemas import DownloadRequest
from app.services.word_generator import generate_word

router = APIRouter(tags=["下载"])

# 下载目录：统一为 ocr-agent/下载
if getattr(sys, "frozen", False):
    _download_dir = Path(sys.executable).parent / "下载"
else:
    _download_dir = Path(__file__).resolve().parent.parent.parent.parent / "下载"
_download_dir.mkdir(exist_ok=True)


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

    filepath = _download_dir / filename
    # 自动编号：如果文件已存在 → 提取结果 (1).docx → 提取结果 (2).docx ...
    stem, ext = filepath.stem, filepath.suffix
    counter = 1
    while filepath.exists():
        filepath = _download_dir / f"{stem} ({counter}){ext}"
        counter += 1
    filepath.write_bytes(file_bytes)
    return {"path": str(filepath), "filename": filepath.name}
