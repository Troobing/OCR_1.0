# OCR Agent

图片文字与公式提取工具。上传图片 → AI 自动提取文字和数学公式（LaTeX） → 一键导出为 Word（.docx，公式可编辑）。

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React 18 + TypeScript + Vite + Ant Design 5 + KaTeX |
| 后端 | Python 3.11+ + FastAPI + Uvicorn |
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

### 2. 打包 exe（一次性）

```powershell
.\build.ps1
```

完成后项目根目录会生成 `OCR-Agent.exe`，双击运行。

> 之后改代码重新打包也只需再跑一次 `.\build.ps1`

### 3. 配置 API

启动后在窗口右上角「API 设置」中填写：

| 字段 | 示例值 |
|------|--------|
| API 地址 | `https://api.uniapi.io/v1` |
| API Key | `sk-xxxx` |
| 模型 | `gpt-4o` |

> 模型必须支持图片识别（Vision）。配置保存在浏览器本地，刷新/重启不丢失。

### 4. 使用流程

1. **上传** — 拖拽 / 点选 / Ctrl+V 粘贴图片（支持 JPG/PNG/WebP/BMP，单张 ≤ 20MB）
2. **提取** — 点击「开始提取」，AI 提取图片中的文字和数学公式
3. **导出** — 复制全文或下载为 Word 文档（公式以 Office 数学格式嵌入，可在 Word 中编辑）

### 开发模式（不改代码不需要看）

如果不想打包 exe，也可以直接跑前后端：

```powershell
# 终端 1 — 后端（自动找空闲端口，5073 被占则用 5074、5075...）
cd ocr-agent\backend
venv\Scripts\python.exe run_dev.py

# 终端 2 — 前端
cd ocr-agent\frontend
npx vite
```

浏览器打开 `http://localhost:5173`。

## 项目结构

```
ocr-agent/
├── README.md
├── build.ps1                       # 一键打包桌面exe
├── .gitignore
│
├── backend/                        # Python FastAPI 后端
│   ├── desktop.py                  # 桌面应用入口
│   ├── app.ico                     # 应用图标
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 # 入口：CORS、路由、静态文件
│       ├── models/schemas.py       # 请求/响应数据结构
│       ├── routers/
│       │   ├── upload.py           # 图片上传
│       │   ├── extract.py          # AI 提取 + 自我校验
│       │   └── download.py         # Word 下载
│       ├── services/
│       │   ├── llm_client.py       # LLM API 调用
│       │   ├── prompt.py           # Prompt 模板
│       │   └── word_generator.py   # Word 生成（LaTeX → OMML）
│       └── utils/
│           └── file_utils.py       # 图片校验、内存存储
│
└── frontend/                       # React + TypeScript 前端
    ├── vite.config.ts              # Vite 构建 + API 代理
    ├── index.html
    └── src/
        ├── main.tsx                # 入口 + 主题色
        ├── App.tsx                 # 主页面
        ├── App.css
        ├── services/
        │   └── api.ts              # HTTP 请求
        └── components/
            ├── UploadZone.tsx       # 上传区域
            ├── ImageList.tsx        # 图片列表
            ├── ApiKeyPanel.tsx      # API 设置
            ├── ResultViewer.tsx     # 结果渲染（KaTeX）
            └── ExportPanel.tsx      # 导出按钮
```

## 工作原理

```
上传图片 → 存到内存 → 返回图片 ID
    ↓
前端发起提取请求（带图片 ID + API 配置）
    ↓
后端：图片 → base64 → 拼 Prompt → 调用 LLM API
    ↓
首轮提取 → 自我校验（原图 + 提取结果发回 AI 校对修正）
    ↓
返回文字 + LaTeX 公式（$...$ 行内 / $$...$$ 块级）
    ↓
前端用 KaTeX 渲染展示
    ↓
用户下载 Word → 后端 LaTeX → MathML → XSLT → OMML → .docx
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/upload` | 上传图片（multipart/form-data, field: files） |
| POST | `/api/extract` | AI 提取文字和公式 |
| POST | `/api/download` | 生成并下载 Word 文档 |

启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 交互式文档。
