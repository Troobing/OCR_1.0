"""
JS Bridge — exe 模式下前端直接调 Python 函数的桥接层
负责：上传、提取、下载、删除图片的桥接实现
Config: 无（下载目录由 file_utils 提供、并发上限由 constants 提供）
（exe 端的所有后端功能入口 — 替代 HTTP 路由）
Skill：pywebview JS API、asyncio.run + gather 并发
"""

import asyncio
import base64

from app.settings import get_config
from app.services.llm_client import extract_from_image
from app.services.word_generator import generate_word
from app.utils.constants import MAX_CONCURRENCY
from app.utils.file_utils import (
    validate_image, save_uploaded_image, get_image_bytes, remove_image,
    get_download_dir, unique_path,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class Bridge:

    def upload_images(self, files: list[dict]) -> list[dict]:
        """files: [{"name":str, "data":base64_str, "size":int, "type":str}, ...]"""
        results = []
        for f in files:
            name = f["name"]
            data = base64.b64decode(f["data"])
            validate_image(name, len(data))
            image_id, width, height = save_uploaded_image(data, name)
            results.append({"id": image_id, "filename": name, "size": len(data),
                            "width": width, "height": height})
        return results

    def delete_image(self, image_id: str) -> bool:
        """删除单张图片（前端删图时同步清理后端内存）"""
        return remove_image(image_id)

    def extract_content(self, image_ids: list[str]) -> list[dict]:
        """API Key 从 .env 读取"""
        cfg = get_config()
        if not cfg["api_key"]:
            return [{"image_id": iid, "filename": "未知", "content": "",
                     "status": "error", "error": "未配置 API Key，请在 .env 文件中设置 LLM_API_KEY"}
                    for iid in image_ids]
        return asyncio.run(self._extract_all(image_ids, cfg))

    async def _extract_all(self, image_ids: list[str], cfg: dict) -> list[dict]:
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

        async def _one(image_id: str) -> dict:
            async with semaphore:
                try:
                    image_data, mime_type = get_image_bytes(image_id)
                except FileNotFoundError:
                    return {"image_id": image_id, "filename": "未知", "content": "",
                            "status": "error", "error": "图片不存在，请重新上传"}
                try:
                    content = await extract_from_image(
                        image_data, mime_type, cfg["api_key"], cfg["base_url"], cfg["model"],
                    )
                    return {"image_id": image_id, "filename": image_id,
                            "content": content, "status": "success", "error": None}
                except Exception as e:
                    logger.exception("提取图片 %s 失败", image_id)
                    return {"image_id": image_id, "filename": "未知", "content": "",
                            "status": "error", "error": str(e)}

        results = await asyncio.gather(*[_one(iid) for iid in image_ids])
        return results

    def download_word(self, image_ids: list[str], contents: list[str],
                      merge: bool = True) -> dict:
        """生成 Word 文档，返回文件路径"""
        d = get_download_dir()
        file_bytes, filename, _ = generate_word(contents, image_ids, merge)
        fp = unique_path(d / filename)
        fp.write_bytes(file_bytes)
        return {"path": str(fp), "filename": fp.name}
