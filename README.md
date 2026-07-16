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

```bash
# 后端
cd backend
python -m venv venv
venv\Scripts\activate      # Windows PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 2. 配置 API

启动后在网页右上角「API 设置」中填写：

| 字段 | 示例值 |
|------|--------|
| API 地址 | `https://api.uniapi.io/v1` |
| API Key | `sk-xxxx` |
| 模型 | `gpt-4o` |

> 模型必须支持图片识别（Vision）。配置自动保存到浏览器本地和后端内存，无需每次填写。

### 3. 启动

```powershell
# 终端 1 — 后端（在 ocr-agent 目录下执行）
cd ocr-agent\backend
venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 终端 2 — 前端（在 ocr-agent 目录下执行）
cd ocr-agent\frontend
npx vite
```

浏览器打开 `http://localhost:5173`。

### 4. 使用流程

1. **上传** — 拖拽 / 点选 / Ctrl+V 粘贴图片（支持 JPG/PNG/WebP/BMP，单张 ≤ 20MB）
2. **提取** — 点击「开始提取」，AI 提取图片中的文字和数学公式
3. **导出** — 复制全文或下载为 Word 文档（公式以 Office 数学格式嵌入，可在 Word 中编辑）

## 项目结构

```
ocr-agent/
├── README.md
│
├── backend/                         # Python FastAPI 后端
│   ├── .env                         # 实际配置（API Key 等，不提交 Git）
│   ├── .env.example                 # 配置模板
│   ├── requirements.txt
│   └── app/
│       ├── main.py                  # 入口：FastAPI 实例、CORS、路由注册
│       ├── models/schemas.py        # Pydantic 数据模型（请求体 & 响应体）
│       ├── routers/
│       │   ├── upload.py            # POST /api/upload   — 图片上传
│       │   ├── extract.py           # POST /api/extract  — AI 提取 + 自我校验
│       │   ├── download.py          # POST /api/download — Word 文件下载
│       │   └── config.py            # POST/GET /api/config — API 配置同步
│       ├── services/
│       │   ├── llm_client.py        # LLM API 调用（图片编码 + 提取 + 校验）
│       │   ├── prompt.py            # System / User / Verify Prompt 模板
│       │   └── word_generator.py    # Word .docx 生成（LaTeX → OMML）
│       └── utils/
│           └── file_utils.py        # 图片校验、保存、清理
│
└── frontend/                        # React + TypeScript 前端
    ├── vite.config.ts               # Vite 构建配置 + /api 代理
    ├── index.html
    └── src/
        ├── main.tsx                 # 入口 + Ant Design 主题色
        ├── App.tsx                  # 主页面：状态管理 + 布局 + 组件拼装
        ├── App.css
        ├── services/
        │   └── api.ts               # HTTP 请求封装
        └── components/
            ├── UploadZone.tsx       # 上传区域（拖拽/点击/粘贴）
            ├── ImageList.tsx        # 图片列表
            ├── ApiKeyPanel.tsx      # API 设置面板
            ├── ResultViewer.tsx     # 结果渲染（KaTeX 公式）
            └── ExportPanel.tsx      # 导出面板（复制/下载）
```

## 工作原理

```
上传图片 → 保存到磁盘 → 返回图片 ID
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
| POST | `/api/config` | 同步 API 配置到后端内存 |
| GET | `/api/config` | 获取后端当前配置 |

启动后端后访问 `http://localhost:8000/docs` 查看 Swagger 交互式文档。
