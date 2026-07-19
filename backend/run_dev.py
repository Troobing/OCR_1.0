"""
开发模式后端启动脚本 — 自动找空闲端口，不用手动改配置
用法：venv/Scripts/python.exe run_dev.py
"""

import socket
import uvicorn
from app.main import app

HOST = "127.0.0.1"
START_PORT = 5073


def find_free_port(start: int) -> int:
    port = start
    while port < start + 100:
        with socket.socket() as s:
            if s.connect_ex((HOST, port)) != 0:
                return port
        port += 1
    raise RuntimeError("找不到空闲端口")


if __name__ == "__main__":
    port = find_free_port(START_PORT)
    if port != START_PORT:
        print(f"端口 {START_PORT} 被占用，自动切换到 {port}")
    print(f"后端启动: http://{HOST}:{port}")
    print(f"如前端无法连接，请修改 vite.config.ts 中的 proxy target 为 http://{HOST}:{port}")
    uvicorn.run(app, host=HOST, port=port)
