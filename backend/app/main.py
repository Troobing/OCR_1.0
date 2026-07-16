"""
OCR Agent — 后端应用入口
负责：FastAPI 实例创建、CORS 跨域配置、路由注册
Config: 路由注册、CORS 白名单、FastAPI 元数据
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ─── FastAPI 应用实例 ───

app = FastAPI(
    title="OCR Agent API",
    description="图片文字与公式提取服务",
    version="1.0.0",
)

# ─── CORS 跨域配置 ───

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 健康检查接口 ───

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "OCR Agent 后端运行中"}

# ─── 路由注册 ───

from app.routers import upload
app.include_router(upload.router, prefix="/api")

from app.routers import extract
app.include_router(extract.router, prefix="/api")

from app.routers import download
app.include_router(download.router, prefix="/api")

from app.routers import config
app.include_router(config.router, prefix="/api")
