"""
OCR Agent — 后端应用入口（开发模式 HTTP）
负责：FastAPI 实例创建、CORS、路由注册
Config: 路由注册、CORS 白名单、FastAPI 元数据
（服务启动）
Skill：FastAPI、CORS
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="OCR Agent", description="图片文字与公式提取工具", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "OCR Agent 后端运行中"}

from app.routers import upload
app.include_router(upload.router, prefix="/api")

from app.routers import extract
app.include_router(extract.router, prefix="/api")

from app.routers import download
app.include_router(download.router, prefix="/api")

from app.routers import config
app.include_router(config.router, prefix="/api")
