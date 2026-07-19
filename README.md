# OCR Agent

图片文字与公式提取工具。上传图片 → AI 自动提取文字和数学公式（LaTeX） → 一键导出为 Word（.docx，公式可编辑）。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design 5 + KaTeX |
| 后端 | Python 3.11+ + FastAPI + Uvicorn |
| 桌面 | pywebview（原生窗口 + JS Bridge，不走 HTTP API） |
| AI | OpenAI 兼容 API（GPT-4o / Claude / Gemini 等） |
| Word | python-docx + latex2mathml + XSLT（OMML 公式） |

## 快速开始

### 1. 安装依赖

```powershell
# 后端（需 Python 3.11+）
cd backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 前端（需 Node.js 18+）
cd frontend
npm install
```

### 2. 打包 exe

```powershell
.\build.ps1
```

完成后项目根目录生成 `OCR-Agent.exe`，双击运行，弹出独立窗口。

之后改代码重新打包只需再跑一次 `.\build.ps1`。

### 3. 配置 API

启动后在窗口右上角「API 设置」中填写：

| 字段 | 示例值 |
|------|--------|
| API 地址 | `https://api.uniapi.io/v1` |
| API Key | `sk-xxxx` |
| 模型 | `gpt-4o` |

> 模型必须支持图片识别（Vision）。exe 端加密存到磁盘 `config.json`，网页端存浏览器 localStorage。两端的配置共用一份加密文件，不会丢失。

### 4. 使用流程

1. **上传** — 拖拽 / 点选 / Ctrl+V 粘贴图片（支持 JPG/PNG/WebP/BMP，单张 ≤ 20MB）
2. **提取** — 点击「开始提取」，AI 提取图片中的文字和数学公式
3. **导出** — 复制全文或下载为 Word 文档。文件保存在 exe 同目录的 `下载` 文件夹中

## exe 与网页端的差异

| | exe 端 | 网页端 |
|---|--------|--------|
| 启动方式 | 双击 `OCR-Agent.exe` | 两个终端分别启动前后端 |
| 通信方式 | JS Bridge（不走 HTTP） | HTTP（axios → FastAPI） |
| 端口 | 随机端口（自动找空闲） | 5073（自动切换） |
| 窗口 | 原生窗口 | 浏览器标签页 |
| 配置存储 | `config.json`（加密） | 浏览器 localStorage |
| 开发者工具 | 无 | F12 可用 |

### 开发模式

```powershell
# 终端 1 — 后端（自动找空闲端口）
cd backend
venv\Scripts\python.exe run_dev.py

# 终端 2 — 前端
cd frontend
npx vite
```

浏览器打开 `http://localhost:5173`。

## 项目结构

```
ocr-agent/
├── README.md
├── build.ps1                         # 一键打包桌面 exe
├── .gitignore
│
├── backend/                          # Python FastAPI 后端
│   ├── desktop.py                    # exe 桌面应用入口
│   ├── run_dev.py                    # 开发模式后端启动脚本
│   ├── app.ico                       # exe 图标
│   ├── requirements.txt
│   └── app/
│       ├── main.py                   # FastAPI 入口（开发模式 HTTP）
│       ├── bridge.py                 # JS Bridge（exe 模式 API）
│       ├── models/schemas.py         # 前后端通信的数据格式
│       ├── routers/
│       │   ├── upload.py             # 图片上传
│       │   ├── extract.py            # AI 提取
│       │   ├── download.py           # Word 下载（网页端）
│       │   └── config.py             # 配置加密读写
│       ├── services/
│       │   ├── llm_client.py         # LLM API 调用
│       │   ├── prompt.py             # Prompt 模板
│       │   └── word_generator.py     # Word 生成（LaTeX → OMML）
│       └── utils/
│           └── file_utils.py         # 图片校验、内存存储
│
└── frontend/                         # React + TypeScript 前端
    ├── vite.config.ts                # Vite 构建 + API 代理
    ├── index.html
    └── src/
        ├── main.tsx                  # 入口 + 粉色主题
        ├── App.tsx                   # 主页面
        ├── App.css
        ├── services/
        │   └── api.ts                # HTTP 请求 + 桥接双模式
        └── components/
            ├── UploadZone.tsx         # 上传区域
            ├── ImageList.tsx          # 图片列表
            ├── ApiKeyPanel.tsx        # API 设置面板
            ├── ResultViewer.tsx       # 结果渲染（KaTeX）
            └── ExportPanel.tsx        # 导出按钮
```

## 工作原理

```
上传图片 → 存到内存 → 返回图片 ID
    ↓
前端调用后端（HTTP 或 JS Bridge）
    ↓
后端：图片 → base64 → 拼 Prompt → 调用 LLM API
    ↓
返回文字 + LaTeX 公式（$...$ 行内 / $$...$$ 块级）
    ↓
前端用 KaTeX 渲染展示
    ↓
下载 Word → LaTeX → MathML → XSLT → OMML → 保存到磁盘
```

## API 接口（开发模式）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/upload` | 上传图片（multipart/form-data, field: files） |
| POST | `/api/extract` | AI 提取文字和公式 |
| POST | `/api/download` | 生成并下载 Word 文档 |

启动后端后访问 `http://localhost:5073/docs` 查看 Swagger 交互式文档。
