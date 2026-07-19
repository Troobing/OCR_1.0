"""
Pydantic 数据模型 — 所有接口的请求体 & 响应体结构
负责：定义前后端通信的数据格式
Config: 上传返回字段、提取请求参数、下载请求格式、配置更新字段
（前端与后端通信的数据格式定义）
Skill：Pydantic BaseModel
"""

from pydantic import BaseModel
from typing import Optional

# ─── 上传接口 /api/upload ───

class ImageInfo(BaseModel):
    """单张图片信息（上传成功后返回，不返回图片本体）"""
    id: str
    filename: str
    size: int
    width: int
    height: int

class UploadResponse(BaseModel):
    images: list[ImageInfo]

# ─── 提取接口 /api/extract ───

class ExtractRequest(BaseModel):
    """提取请求：仅传图片 ID。API Key 由后端从 config.json 读取，前端不接触明文 key。"""
    image_ids: list[str]

class ExtractResult(BaseModel):
    """单张图片提取结果"""
    image_id: str
    filename: str
    content: str
    status: str
    error: Optional[str] = None

class ExtractResponse(BaseModel):
    results: list[ExtractResult]

# ─── 下载接口 /api/download ───

class DownloadRequest(BaseModel):
    """Word 下载请求"""
    image_ids: list[str]
    contents: list[str]
    merge: bool = True

# ─── 配置接口 /api/config ───

class ConfigUpdateRequest(BaseModel):
    """配置增量更新请求。所有字段可选，未传字段保留原值。"""
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
