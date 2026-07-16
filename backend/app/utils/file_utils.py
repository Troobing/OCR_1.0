"""
文件工具 — 图片校验、保存、获取路径、删除、过期清理
Config: 允许的图片格式、大小上限、存储路径
"""

import os
import uuid
from pathlib import Path
from PIL import Image

# ─── 常量 ───

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_FILE_SIZE = 20 * 1024 * 1024

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
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / unique_name
    with open(file_path, "wb") as f:
        f.write(file_data)
    with Image.open(file_path) as img:
        width, height = img.size
    return unique_name, width, height

def get_image_path(image_id: str) -> Path:
    return UPLOAD_DIR / image_id

def delete_image(image_id: str) -> None:
    file_path = UPLOAD_DIR / image_id
    if file_path.exists():
        file_path.unlink()

def cleanup_old_files(max_age_hours: int = 24) -> int:
    import time
    count = 0
    cutoff = time.time() - max_age_hours * 3600
    for file_path in UPLOAD_DIR.iterdir():
        if file_path.is_file() and file_path.stat().st_mtime < cutoff:
            file_path.unlink()
            count += 1
    return count
