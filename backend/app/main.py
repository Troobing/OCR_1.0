"""
OCR Agent — 后端应用入口
负责：FastAPI 实例创建、CORS 跨域配置、路由注册
Config: 路由注册、CORS 白名单、FastAPI 元数据
（服务启动 — 双击exe时最先执行的文件）
Skill：FastAPI、CORS、StaticFiles
"""

import sys
import mimetypes
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Windows Python 缺 JS/CSS 的 MIME → 补上，否则浏览器拒绝加载
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")

# PyInstaller 打包后文件在 sys._MEIPASS，开发模式用相对路径
if getattr(sys, "frozen", False):
    FRONTEND_DIST = Path(sys._MEIPASS) / "frontend" / "dist"
else:
    FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

# ─── FastAPI 应用实例 ───

app = FastAPI(
    title="OCR Agent",
    description="图片文字与公式提取工具",
    version="1.0.0",
)

# ─── CORS 跨域配置 ───

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 健康检查接口 ───

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "OCR Agent 后端运行中"}

# ─── API 路由注册（必须在 StaticFiles mount 之前）───

from app.routers import upload
app.include_router(upload.router, prefix="/api")

from app.routers import extract
app.include_router(extract.router, prefix="/api")

from app.routers import download
app.include_router(download.router, prefix="/api")

from app.routers import config
app.include_router(config.router, prefix="/api")

# ─── 前端静态文件（仅在生产模式，dist/ 存在时生效）───

if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
