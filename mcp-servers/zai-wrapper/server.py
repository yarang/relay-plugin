# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "zhipuai>=2.1.0",
#   "pydantic>=2.0.0",
# ]
# ///
"""
relay zai-wrapper MCP server
Zhipu AI GLM 시리즈를 relay의 backed_by: zai:* 네임스페이스로 노출합니다.

실행: uv run server.py
환경 변수: ZHIPU_API_KEY
"""

import os
from typing import Optional

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from zhipuai import ZhipuAI

mcp = FastMCP("zai_mcp")


class GenerateInput(BaseModel):
    prompt: str
    model: str = "glm-4-flash"          # 기본값: 무료 티어
    system: Optional[str] = None         # 페르소나 합성 결과
    context: Optional[str] = None        # 압축된 배경 컨텍스트 (raw history 금지)
    temperature: float = 0.7
    max_tokens: int = 4096


@mcp.tool()
def zai_generate(
    prompt: str,
    model: str = "glm-4-flash",
    system: Optional[str] = None,
    context: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """
    Zhipu AI GLM 모델로 텍스트를 생성합니다.

    Args:
        prompt:      이번 task 지시문
        model:       GLM 모델명 (glm-4-flash / glm-4-air / glm-4 / glm-4-long)
        system:      페르소나 합성 결과 (전문가 파일의 페르소나+역량+제약)
        context:     이전 작업의 압축 요약 (raw 대화 기록 금지)
        temperature: 생성 온도 (0.0~1.0)
        max_tokens:  최대 출력 토큰
    """
    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        raise ValueError(
            "ZHIPU_API_KEY 환경 변수가 설정되지 않았습니다.\n"
            "/relay:setup-keys 를 실행하여 API 키를 등록하세요."
        )

    client = ZhipuAI(api_key=api_key)

    # system + context 합성 → one-shot
    system_content = system or "You are a helpful assistant."
    if context:
        system_content = f"{system_content}\n\n## 배경 컨텍스트\n{context}"

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user",   "content": prompt},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    mcp.run()
