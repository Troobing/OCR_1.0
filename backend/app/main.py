"""
OCR Agent — 后端应用入口（开发模式 HTTP）
负责：FastAPI 实例创建、CORS、路由注册
Config: 路由注册、CORS 白名单、FastAPI 元数据
（服务启动 — 双击 exe 时最先执行的文件）
Skill：FastAPI、CORS
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import upload, extract, download, config, image

app = FastAPI(title="OCR Agent", description="图片文字与公式提取工具", version="1.0.0")

# CORS 仅用于开发模式（前端走 Vite 5173 直连后端 5073）
# exe 模式下前端与静态服务同源，且 API 走 JS Bridge，不经 HTTP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(upload.router, prefix="/api")
app.include_router(image.router, prefix="/api")
app.include_router(extract.router, prefix="/api")
app.include_router(download.router, prefix="/api")
app.include_router(config.router, prefix="/api")
