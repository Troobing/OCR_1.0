"""
桌面应用入口 — 静态文件用随机端口 HTTP 服务，API 走 JS Bridge
"""

import sys
import socket
import mimetypes
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import webview
from app.bridge import Bridge

# Windows Python 缺 JS/CSS 的 MIME → 补上
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")

if getattr(sys, "frozen", False):
    _dist = Path(sys._MEIPASS) / "frontend" / "dist"
else:
    _dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"


def _random_port() -> int:
    """获取一个空闲的随机端口"""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_static_server(port: int):
    """仅提供静态文件，API 不走这里"""
    import os
    os.chdir(_dist)
    httpd = HTTPServer(("127.0.0.1", port), SimpleHTTPRequestHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    bridge = Bridge()
    port = _random_port()

    # 后台启动纯静态文件服务（无 API，只提供 HTML/JS/CSS）
    threading.Thread(target=_start_static_server, args=(port,), daemon=True).start()

    # API 走桥接，文件走 HTTP：没有端口冲突风险（用随机端口），没有 Edge 错误页
    webview.create_window(
        "OCR Agent",
        url=f"http://127.0.0.1:{port}",
        js_api=bridge,
        width=1200, height=800, min_size=(800, 600),
    )
    webview.start()
