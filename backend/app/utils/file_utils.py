"""
文件工具 — 图片校验、内存存储（LRU + 容量上限）、获取/删除图片数据
负责：上传校验、内存缓存管理、下载目录路径
Config: 允许的图片格式、大小上限、内存存储容量上限、下载目录
（所有端共用 — HTTP 路由和 Bridge 都调它）
Skill：PIL.Image、OrderedDict LRU、路径分流
"""

import os
import sys
import io
import uuid
from pathlib import Path
from collections import OrderedDict
from PIL import Image

# ─── 常量 ───

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_FILE_SIZE = 20 * 1024 * 1024
# 内存存储总容量上限：超过则按 LRU 淘汰最老的图片
_MAX_STORE_BYTES = 500 * 1024 * 1024

# 扩展名 → MIME 类型映射（与 ALLOWED_EXTENSIONS 同源，新增格式需同步两处）
_MIME_MAP = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".webp": "image/webp", ".bmp": "image/bmp",
}

# 内存存储：image_id → (bytes, filename)，按 LRU 顺序排列（最老在前）
_image_store: "OrderedDict[str, tuple[bytes, str]]" = OrderedDict()

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
            f"文件过大（{file_size / 1024 / 1024:.1f}MB），最大允许 {MAX_FILE_SIZE // 1024 // 1024}MB"
        )

def _current_store_bytes() -> int:
    return sum(len(data) for data, _ in _image_store.values())

def _evict_until_fit(extra_bytes: int) -> None:
    """淘汰最老的条目，直到加入 extra_bytes 后总量不超过上限。"""
    while _image_store and (_current_store_bytes() + extra_bytes > _MAX_STORE_BYTES):
        _image_store.popitem(last=False)  # FIFO 淘汰最老

def save_uploaded_image(file_data: bytes, original_filename: str) -> tuple[str, int, int]:
    ext = get_extension(original_filename)
    image_id = f"{uuid.uuid4().hex}{ext}"
    _evict_until_fit(len(file_data))
    _image_store[image_id] = (file_data, original_filename)
    _image_store.move_to_end(image_id)  # 新写入放最末（最新）
    with Image.open(io.BytesIO(file_data)) as img:
        width, height = img.size
    return image_id, width, height

def get_image_bytes(image_id: str) -> tuple[bytes, str]:
    """返回 (图片二进制数据, MIME类型如 image/png)。命中后标记为最近使用。"""
    if image_id not in _image_store:
        raise FileNotFoundError(f"图片 {image_id} 不存在，请重新上传")
    data, _ = _image_store[image_id]
    _image_store.move_to_end(image_id)  # LRU：命中后移到最新
    ext = get_extension(image_id)
    return data, _MIME_MAP.get(ext, "image/png")

def remove_image(image_id: str) -> bool:
    """删除指定图片。返回是否实际删除了条目。"""
    if image_id in _image_store:
        del _image_store[image_id]
        return True
    return False


# ─── 下载目录路径工具（bridge.py 与 download.py 共用）───

def get_download_dir() -> Path:
    """返回下载目录路径（frozen/非 frozen 自动分流）。目录不存在则创建。"""
    if getattr(sys, "frozen", False):
        d = Path(sys.executable).parent / "下载"
    else:
        d = Path(__file__).resolve().parent.parent.parent.parent / "下载"
    d.mkdir(parents=True, exist_ok=True)
    return d

def unique_path(path: Path) -> Path:
    """文件已存在则自动编号 (1)(2)...，避免覆盖。"""
    if not path.exists():
        return path
    stem, suffix, parent = path.stem, path.suffix, path.parent
    n = 1
    while True:
        candidate = parent / f"{stem} ({n}){suffix}"
        if not candidate.exists():
            return candidate
        n += 1
