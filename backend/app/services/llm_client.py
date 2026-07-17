"""
LLM 客户端 — 图片 base64 编码 + 调用 OpenAI 兼容 API 提取图文内容
Config: base_url、model、temperature、max_tokens、frequency_penalty
（真正调用 AI 的环节）
"""

import base64
from openai import OpenAI
from app.services.prompt import SYSTEM_PROMPT, USER_PROMPT


# ─── 核心函数 ───

async def extract_from_image(
    image_data: bytes,
    mime_type: str,
    api_key: str,
    base_url: str = "https://api.deepseek.com/v1",
    model: str = "deepseek-chat",
) -> str:
    """将图片发给 LLM，返回提取到的文字 + LaTeX 公式"""
    encoded = base64.b64encode(image_data).decode("utf-8")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": USER_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
            ],
        },
    ]

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        max_tokens=32768,
        frequency_penalty=0.2,
    )

    content = response.choices[0].message.content
    if content is None:
        raise ValueError("AI 未返回任何内容，请重试")
    return content