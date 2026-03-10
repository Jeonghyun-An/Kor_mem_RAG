"""
LLM 서비스 - vLLM OpenAI 호환 스트리밍
"""
from __future__ import annotations
import os
from typing import AsyncGenerator
from openai import AsyncOpenAI

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:18082")
VLLM_MODEL    = os.getenv("VLLM_MODEL_NAME", "gemma-3-12b")
MAX_TOKENS    = int(os.getenv("RAG_MAX_TOKENS", "4000"))

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=f"{VLLM_BASE_URL}/v1",
            api_key="not-needed",
        )
    return _client


async def stream_llm(query: str, context: str) -> AsyncGenerator[str, None]:
    """
    chat_router.py에서 완성된 프롬프트(context)를 그대로 user 메시지로 전달.
    system prompt 없음 - Gemma는 chat_router의 <start_of_turn> 템플릿으로 제어.
    """
    try:
        client = _get_client()
        stream = await client.chat.completions.create(
            model=VLLM_MODEL,
            messages=[
                {"role": "user", "content": context},  # chat_router 프롬프트 그대로
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.3,
            stream=True,
            stop=["📚", "<end_of_turn>", "<eos>"],
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    except Exception as e:
        yield f"\n\nLLM 오류: {e}"