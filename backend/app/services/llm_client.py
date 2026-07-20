"""
LLM 客户端 — 图片 base64 编码 + 调用 OpenAI 兼容 API 提取图文内容
负责：异步调用 LLM、超时与重试、prompt 拼装
Config: timeout、重试次数与退避、temperature、max_tokens
（所有端共用 — HTTP 和 Bridge 都调它）
Skill：AsyncOpenAI、base64、Data URL、指数退避
"""

import asyncio
import base64

from openai import AsyncOpenAI, APITimeoutError, RateLimitError, APIConnectionError, InternalServerError, APIStatusError

from app.services.prompt import SYSTEM_PROMPT, USER_PROMPT
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ─── 调用参数 ───

_TIMEOUT = 120.0              # 单次请求超时（秒），与前端 axios 对齐
_MAX_RETRIES = 2              # 最大重试次数（不含首次）
_RETRY_DELAYS = [0.5, 2.0]    # 指数退避间隔（秒）
# 可重试的异常类型（瞬时错误）
_RETRYABLE = (APITimeoutError, RateLimitError, APIConnectionError, InternalServerError)


async def extract_from_image(
    image_data: bytes,
    mime_type: str,
    api_key: str,
    base_url: str = "https://api.uniapi.io/v1",
    model: str = "gpt-4o",
) -> str:
    """将图片发给 LLM，返回提取到的文字 + LaTeX 公式。

    每次调用内复用单个 AsyncOpenAI 实例；超时或瞬时错误指数退避重试。
    """
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

    # 请求内复用 client（AsyncOpenAI 实例绑定当前事件循环，不跨请求缓存）
    client = AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=_TIMEOUT)

    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=16384,
                # frequency_penalty=0：避免抑制公式中重复符号（a_1+a_2+...+a_n）
                frequency_penalty=0,
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("AI 未返回任何内容，请重试")
            return content
        except _RETRYABLE as e:
            last_exc = e
            if attempt < _MAX_RETRIES:
                delay = _RETRY_DELAYS[attempt]
                logger.warning(
                    "LLM 调用失败（第 %d/%d 次），%.1fs 后重试：%s",
                    attempt + 1, _MAX_RETRIES, delay, e,
                )
                await asyncio.sleep(delay)
                continue
            break
        except APIStatusError as e:
            # 4xx（除 429）等不可重试错误，直接抛出
            last_exc = e
            break
        except Exception as e:
            last_exc = e
            logger.exception("LLM 调用发生未预期错误")
            break

    # 走到这里说明重试用尽或不可重试错误，统一关闭 client
    try:
        await client.close()
    except Exception:
        pass
    if last_exc:
        raise last_exc
    raise RuntimeError("LLM 调用失败，未知原因")
