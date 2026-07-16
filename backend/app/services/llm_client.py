"""
LLM 客户端 — 图片 base64 编码 + 调用 OpenAI 兼容 API 提取图文内容
Config: base_url、model、temperature、max_tokens、frequency_penalty
"""

import base64
import mimetypes
from openai import OpenAI
from app.services.prompt import SYSTEM_PROMPT, USER_PROMPT, VERIFY_PROMPT


# ─── 核心函数 ───

async def extract_from_image(
    image_path: str,
    api_key: str,
    base_url: str = "https://api.deepseek.com/v1",
    model: str = "deepseek-chat",
) -> str:
    """
    将图片发给 LLM，返回提取到的文字 + LaTeX 公式。
    流程：图片 base64 编码 → 拼 System/User Prompt → 调用 API → 返回文本
    """
    encoded_image = _encode_image_to_base64(image_path)
    mime_type = _get_mime_type(image_path)

    # 构造 OpenAI 兼容的消息格式
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": USER_PROMPT},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"},
                },
            ],
        },
    ]

    # 每次新建 client，支持不同用户使用不同 API Key
    client = OpenAI(api_key=api_key, base_url=base_url)

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,       # 0.3 比 0.1 更能打破重复循环
        max_tokens=32768,      # 文字密集的图片需要较大上限
        frequency_penalty=0.2,  # 轻度抑制重复词
    )

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("AI 未返回任何内容，请重试")
    return content


# ─── 自我校验 — Agent 第二步：对照原图修正错误 ───

async def verify_extraction(
    image_path: str,
    extracted_text: str,
    api_key: str,
    base_url: str = "https://api.deepseek.com/v1",
    model: str = "deepseek-chat",
) -> tuple[str, bool]:
    """
    把首次提取结果 + 原图一起发给 AI 校对一遍，返回 (修正后文本, 是否有改动)。
    is_corrected=True 表示 AI 做了一定修正。
    """
    encoded_image = _encode_image_to_base64(image_path)
    mime_type = _get_mime_type(image_path)

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"{VERIFY_PROMPT}\n\n=== 原图提取结果 ===\n{extracted_text}\n=== 请对照原图修正以上内容 ===",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{encoded_image}"},
                },
            ],
        },
    ]

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,       # 比首次提取更低——校对要精确，不要发挥
        max_tokens=32768,
    )

    verified_content = response.choices[0].message.content
    if verified_content is None:
        raise ValueError("AI 校验未返回任何内容")

    is_corrected = (verified_content.strip() != extracted_text.strip())
    return verified_content, is_corrected

# ─── 辅助函数 ───

def _encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as f:
        image_data = f.read()
    return base64.b64encode(image_data).decode("utf-8")


def _get_mime_type(image_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    return mime_type or "image/png"
