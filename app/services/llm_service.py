"""
LLM 서비스 - vLLM OpenAI 호환 스트리밍
"""
from __future__ import annotations
import os
from typing import AsyncGenerator
from openai import AsyncOpenAI

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:18082")
VLLM_MODEL    = os.getenv("VLLM_MODEL_NAME", "exaone")
MAX_TOKENS    = int(os.getenv("RAG_MAX_TOKENS", "1500"))

_client: AsyncOpenAI | None = None

SYSTEM_PROMPT = """당신은 코리안메모리(Korean Memory) 플랫폼의 AI 도우미입니다.
코리안메모리는 국립중앙도서관이 운영하는 한국 문화 콘텐츠 아카이브입니다.

## 역할
제공된 참고 자료만을 기반으로 사용자의 질문에 한국어로 답변합니다.

## 규칙
1. 반드시 제공된 [참고 자료] 내용만 사용하세요.
2. 자료에 없는 내용은 "제공된 자료에서 찾을 수 없습니다"라고 답하세요.
3. 답변 마지막에 출처를 명시하세요.
4. 마크다운 형식으로 답변하세요.

## 출처 표기 형식
📚 **참고 자료**
- [콘텐츠 제목] (배지 유형)
"""


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=f"{VLLM_BASE_URL}/v1",
            api_key="not-needed",
        )
    return _client


async def stream_llm(query: str, context: str) -> AsyncGenerator[str, None]:
    """LLM 스트리밍 토큰 생성기"""
    user_prompt = f"""다음 참고 자료를 바탕으로 질문에 답해주세요.

[참고 자료]
{context}

[질문]
{query}

[답변]"""

    try:
        client = _get_client()
        stream = await client.chat.completions.create(
            model=VLLM_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.3,
            stream=True,
        )

        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    except Exception as e:
        yield f"\n\n⚠️ LLM 오류: {e}"
