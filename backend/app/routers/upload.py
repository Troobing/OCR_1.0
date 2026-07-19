"""
上传路由 — POST /api/upload
负责：接收图片文件 → 校验格式/大小 → 存到内存 → 返回图片元信息
Config: 文件格式白名单、大小上限
（网页端的图片上传功能）
Skill：FastAPI UploadFile、multipart
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import UploadResponse, ImageInfo
from app.utils import file_utils

router = APIRouter(tags=["上传"])


@router.post("/upload", response_model=UploadResponse)
async def upload_images(files: list[UploadFile] = File(...)):
    """上传一张或多张图片，返回每张图片的 ID、尺寸等信息"""
    if not files:
        raise HTTPException(status_code=400, detail="请至少上传一张图片")

    images = []
    for file in files:
        file_data = await file.read()

        # 校验格式和大小
        try:
            file_utils.validate_image(file.filename, len(file_data))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # 保存到磁盘
        try:
            image_id, width, height = file_utils.save_uploaded_image(
                file_data, file.filename
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"保存文件 '{file.filename}' 失败：{str(e)}")

        images.append(ImageInfo(
            id=image_id,
            filename=file.filename,
            size=len(file_data),
            width=width,
            height=height,
        ))

    return UploadResponse(images=images)
