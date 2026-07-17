"""
桌面应用入口 — 双击启动后端 + 原生窗口
Config: 端口、窗口大小、Edge 路径
（双击 exe 时最先执行的文件）
"""

import threading
import time
import urllib.request
import uvicorn
import webview
from app.main import app

HOST = "127.0.0.1"
PORT = 8000


def start_server():
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    url = f"http://{HOST}:{PORT}"
    for _ in range(30):
        try:
            urllib.request.urlopen(url + "/api/health")
            break
        except Exception:
            time.sleep(0.3)

    webview.create_window("OCR Agent", url, width=1200, height=800, min_size=(800, 600))
    webview.start()
