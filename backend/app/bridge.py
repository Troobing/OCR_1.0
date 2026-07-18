"""
JS Bridge — 暴露给 pywebview 前端的 Python 函数
exe 模式下前端不调 HTTP，通过 window.pywebview.api.xxx() 直接调这些函数
"""

import base64
import asyncio
from pathlib import Path
from app.utils.file_utils import validate_image, save_uploaded_image, get_image_bytes
from app.services.llm_client import extract_from_image
from app.services.word_generator import generate_word
from app.routers.config import _read_config, CONFIG_FILE
import json


class Bridge:
    """所有需要暴露给前端的方法都写在这里，pywebview 会自动挂到 window.pywebview.api"""

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

    def extract_content(self, image_ids: list[str], api_key: str,
                        base_url: str = "https://api.uniapi.io/v1",
                        model: str = "gpt-4o") -> list[dict]:
        """逐张提取，返回结果列表"""
        results = []
        for image_id in image_ids:
            try:
                image_data, mime_type = get_image_bytes(image_id)
            except FileNotFoundError:
                results.append({"image_id": image_id, "filename": "未知", "content": "",
                                "status": "error", "error": "图片不存在，请重新上传"})
                continue
            try:
                content = asyncio.run(
                    extract_from_image(image_data, mime_type, api_key, base_url, model)
                )
                results.append({"image_id": image_id, "filename": image_id,
                                "content": content, "status": "success", "error": None})
            except Exception as e:
                results.append({"image_id": image_id, "filename": "未知", "content": "",
                                "status": "error", "error": str(e)})
        return results

    def download_word(self, image_ids: list[str], contents: list[str],
                      merge: bool = True) -> dict:
        """生成 Word 文档，返回文件路径"""
        import sys
        if getattr(sys, "frozen", False):
            d = Path(sys.executable).parent / "下载"
        else:
            d = Path(__file__).resolve().parent.parent.parent / "下载"
        d.mkdir(exist_ok=True)

        file_bytes, filename, _ = generate_word(contents, image_ids, merge)
        fp = d / filename
        stem, ext = fp.stem, fp.suffix
        counter = 1
        while fp.exists():
            fp = d / f"{stem} ({counter}){ext}"
            counter += 1
        fp.write_bytes(file_bytes)
        return {"path": str(fp), "filename": fp.name}

    def save_config(self, base_url: str, api_key: str, model: str):
        CONFIG_FILE.write_text(json.dumps(
            {"base_url": base_url, "api_key": api_key, "model": model},
            ensure_ascii=False, indent=2), encoding="utf-8")

    def load_config(self) -> dict:
        return _read_config()
