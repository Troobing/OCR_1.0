"""
Pydantic 数据模型 — 所有接口的请求体 & 响应体结构
负责：定义前后端通信的数据格式
Config: 上传返回字段、提取请求参数、下载请求格式
（前端与后端通信的数据格式定义）
Skill：Pydantic BaseModel
"""

from pydantic import BaseModel
from typing import Optional

# ─── 上传接口 /api/upload ───

class ImageInfo(BaseModel):
    id: str
    filename: str
    size: int
    width: int
    height: int

class UploadResponse(BaseModel):
    images: list[ImageInfo]

# ─── 提取接口 /api/extract ───

class ExtractRequest(BaseModel):
    """API Key 从 .env 读取，前端不传"""
    image_ids: list[str]

class ExtractResult(BaseModel):
    image_id: str
    filename: str
    content: str
    status: str
    error: Optional[str] = None

class ExtractResponse(BaseModel):
    results: list[ExtractResult]

# ─── 下载接口 /api/download ───

class DownloadRequest(BaseModel):
    image_ids: list[str]
    contents: list[str]
    merge: bool = True
