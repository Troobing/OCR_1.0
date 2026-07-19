"""
配置服务 — API 配置的统一读写 + 加解密
负责：config.json 持久化、API Key 加密（Windows 走 DPAPI，其他平台回退 XOR）
Config: 配置文件路径、默认值、加密策略
（所有端共用 — HTTP 路由和 Bridge 都调它）
Skill：DPAPI(crypt32.dll)、平台分流、增量更新
"""

import sys
import json
import base64
import hashlib
import platform
import ctypes
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger(__name__)

# ─── 配置文件路径 ───

if getattr(sys, "frozen", False):
    CONFIG_FILE = Path(sys.executable).parent / "config.json"
else:
    CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "config.json"

DEFAULTS = {"base_url": "https://api.uniapi.io/v1", "api_key": "", "model": "gpt-4o"}

# ─── 加密策略：Windows 走 DPAPI（OS 当前用户保管密钥），其他平台退回 XOR ───

def _is_windows() -> bool:
    return sys.platform == "win32" and hasattr(ctypes, "windll")


# DPAPI 调用：crypt32.dll 的 CryptProtectData / CryptUnprotectData
# 密钥由 Windows 当前用户保管，换机/换用户自动解不开
class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", ctypes.c_ulong),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def _dpapi_protect(data: bytes) -> bytes:
    in_blob = _DATA_BLOB(len(data), ctypes.cast(ctypes.c_char_p(data), ctypes.POINTER(ctypes.c_char)))
    out_blob = _DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(in_blob), "ocr_agent_key", None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise OSError("CryptProtectData 失败")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


def _dpapi_unprotect(data: bytes) -> bytes:
    in_blob = _DATA_BLOB(len(data), ctypes.cast(ctypes.c_char_p(data), ctypes.POINTER(ctypes.c_char)))
    out_blob = _DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)
    ):
        raise OSError("CryptUnprotectData 失败")
    try:
        return ctypes.string_at(out_blob.pbData, out_blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(out_blob.pbData)


# 非 Windows 平台的兜底：本机特征派生密钥做 XOR 混淆（仅防误读，不防本地攻击）
# 懒加载：Windows 平台永远走 DPAPI，不必在模块加载时就算 sha256
_FALLBACK_KEY: bytes | None = None


def _get_fallback_key() -> bytes:
    global _FALLBACK_KEY
    if _FALLBACK_KEY is None:
        _FALLBACK_KEY = hashlib.sha256(f"{platform.node()}{platform.machine()}".encode()).digest()
    return _FALLBACK_KEY


def _xor_encrypt(data: bytes) -> bytes:
    key = _get_fallback_key()
    return bytes(a ^ key[i % len(key)] for i, a in enumerate(data))


def _encrypt(text: str) -> str:
    """加密字符串为 base64 文本。空串返回空串。"""
    if not text:
        return ""
    data = text.encode("utf-8")
    if _is_windows():
        try:
            encrypted = _dpapi_protect(data)
        except OSError as e:
            logger.warning(f"DPAPI 加密失败，退回 XOR：{e}")
            encrypted = _xor_encrypt(data)
    else:
        encrypted = _xor_encrypt(data)
    return base64.b64encode(encrypted).decode("ascii")


def _decrypt(encoded: str) -> str:
    """解密 base64 文本。空串返回空串。解密失败返回空串（不抛异常）。"""
    if not encoded:
        return ""
    try:
        data = base64.b64decode(encoded)
        if _is_windows():
            try:
                decrypted = _dpapi_unprotect(data)
            except OSError as e:
                # 可能是旧版本用 XOR 加密的，尝试兜底解密
                logger.warning(f"DPAPI 解密失败，尝试 XOR 兜底：{e}")
                decrypted = _xor_encrypt(data)
        else:
            decrypted = _xor_encrypt(data)
        return decrypted.decode("utf-8")
    except Exception as e:
        logger.warning(f"解密 API Key 失败：{e}")
        return ""


# ─── 对外 API ───

def read_config() -> dict:
    """读取完整配置（含解密后的明文 api_key）。失败返回 DEFAULTS。"""
    try:
        cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        return {
            "base_url": cfg.get("base_url") or DEFAULTS["base_url"],
            "api_key": _decrypt(cfg.get("api_key", "")),
            "model": cfg.get("model") or DEFAULTS["model"],
        }
    except Exception:
        return dict(DEFAULTS)


def read_config_masked() -> dict:
    """读取配置，api_key 返回掩码（****1234 或空），并附 has_key 标记。前端安全用。"""
    cfg = read_config()
    key = cfg["api_key"]
    if key:
        mask = "****" + key[-4:] if len(key) >= 4 else "****"
    else:
        mask = ""
    return {
        "base_url": cfg["base_url"],
        "model": cfg["model"],
        "api_key": mask,
        "has_key": bool(key),
    }


def save_config(base_url: str | None = None, api_key: str | None = None, model: str | None = None) -> dict:
    """增量保存配置。

    - base_url / model 为 None 时不覆盖原值
    - api_key 为 None 或空字符串时不覆盖原 key（避免前端掩码误覆盖真值）
    - api_key 非空时覆盖
    返回保存后的完整配置（含明文 key）。
    """
    current = read_config()
    new_base_url = base_url if base_url is not None else current["base_url"]
    new_model = model if model is not None else current["model"]
    if api_key:  # 非空才覆盖
        new_api_key = api_key
    else:
        new_api_key = current["api_key"]

    payload = {
        "base_url": new_base_url,
        "api_key": _encrypt(new_api_key),
        "model": new_model,
    }
    CONFIG_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info("配置已保存（api_key %s）", "已更新" if api_key else "保留原值")
    return {"base_url": new_base_url, "api_key": new_api_key, "model": new_model}
