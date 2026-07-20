"""
应用配置 — 从 .env 文件读取 LLM API 设置
负责：.env 解析、默认值回退
Config: 文件路径、默认值
（所有端共用）
Skill：文件解析
"""

import sys
from pathlib import Path

# 配置文件路径：exe 内打包 .env 在 _MEIPASS，开发时在 backend/
if getattr(sys, "frozen", False):
    ENV_FILE = Path(sys._MEIPASS) / ".env"
else:
    ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

DEFAULTS = {
    "base_url": "https://api.uniapi.io/v1",
    "api_key": "",
    "model": "gpt-4o",
}


def _parse_env(path: Path) -> dict[str, str]:
    """简化的 key=value 解析，不引入 python-dotenv 依赖"""
    result = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip().strip('"').strip("'")
    return result


def get_config() -> dict[str, str]:
    """读取配置，未设置的项取默认值"""
    env = _parse_env(ENV_FILE)
    return {
        "base_url": env.get("LLM_BASE_URL") or DEFAULTS["base_url"],
        "api_key": env.get("LLM_API_KEY") or DEFAULTS["api_key"],
        "model": env.get("LLM_MODEL") or DEFAULTS["model"],
    }
