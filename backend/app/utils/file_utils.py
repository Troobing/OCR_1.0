"""
文件工具 — 图片校验、内存存储、获取图片数据
Config: 允许的图片格式、大小上限
（上传时校验图片 + 提取时提供图片数据）
"""

import os
import io
import uuid
from PIL import Image

# ─── 常量 ───

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_FILE_SIZE = 20 * 1024 * 1024

# 内存存储：image_id → (bytes, filename)
_image_store: dict[str, tuple[bytes, str]] = {}

# ─── 工具函数 ───

def get_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()

def validate_image(filename: str, file_size: int) -> None:
    ext = get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"不支持的文件格式 '{ext}'，仅支持：{', '.join(ALLOWED_EXTENSIONS)}"
        )
    if file_size > MAX_FILE_SIZE:
        raise ValueError(
            f"文件过大（{file_size / 1024 / 1024:.1f}MB），最大允许 20MB"
        )

def save_uploaded_image(file_data: bytes, original_filename: str) -> tuple[str, int, int]:
    ext = get_extension(original_filename)
    image_id = f"{uuid.uuid4().hex}{ext}"
    _image_store[image_id] = (file_data, original_filename)
    with Image.open(io.BytesIO(file_data)) as img:
        width, height = img.size
    return image_id, width, height

def get_image_bytes(image_id: str) -> tuple[bytes, str]:
    """返回 (图片二进制数据, MIME类型如 image/png)"""
    if image_id not in _image_store:
        raise FileNotFoundError(f"图片 {image_id} 不存在，请重新上传")
    data, _ = _image_store[image_id]
    ext = get_extension(image_id)
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
                ".webp": "image/webp", ".bmp": "image/bmp"}
    return data, mime_map.get(ext, "image/png")
