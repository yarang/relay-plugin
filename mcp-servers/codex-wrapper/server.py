# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "openai>=1.50.0",
#   "pydantic>=2.0.0",
# ]
# ///
"""
codex_mcp — OpenAI API wrapper for Claude Code / relay plugin
(GPT-4o, o1, o3, Codex 계열 모델 지원)

실행 방법:
  uv run server.py          # 의존성 자동 설치 후 실행
  uv run --python 3.11 server.py  # Python 버전 지정
"""

import os
from typing import Optional, Literal
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("codex_mcp")


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class GenerateInput(BaseModel):
    prompt: str = Field(..., description="현재 요청. 작업 지시문을 명확하게 작성합니다.")
    model: str = Field(
        default="gpt-4o",
        description=(
            "사용할 OpenAI 모델. 예: gpt-4o, gpt-4o-mini, o1, o3-mini, "
            "codex-davinci-002 (레거시)"
        ),
    )
    system: str = Field(
        default="You are a helpful assistant.",
        description="역할·제약·출력 형식 등 정적 지침",
    )
    context: Optional[str] = Field(
        default=None,
        description=(
            "이전 작업 결과·배경 정보의 요약 (선택). "
            "raw 대화 기록 대신 호출자(Claude Code)가 직접 압축한 컨텍스트를 전달합니다. "
            "system 뒤에 붙어 최종 시스템 메시지를 구성합니다. "
            "예: '이전에 작성한 계약서 초안 요약: [...]. 검토 포인트: 위약금 조항'"
        ),
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="생성 다양성 (0.0~2.0). o1/o3 계열은 무시됩니다.",
    )
    max_tokens: int = Field(
        default=4096,
        ge=1,
        le=128000,
        description="최대 출력 토큰 수",
    )
    response_format: Literal["text", "json_object"] = Field(
        default="text",
        description="응답 형식. json_object 지정 시 JSON 구조 반환",
    )


class CodeReviewInput(BaseModel):
    code: str = Field(..., description="리뷰할 코드")
    language: str = Field(default="python", description="프로그래밍 언어")
    focus: str = Field(
        default="전반적인 품질, 버그, 개선점",
        description="리뷰 집중 항목. 예: 보안, 성능, 테스트 가능성",
    )
    model: str = Field(default="gpt-4o", description="사용할 모델")


class EmbedInput(BaseModel):
    text: str = Field(..., description="임베딩할 텍스트")
    model: str = Field(
        default="text-embedding-3-small",
        description="임베딩 모델. 예: text-embedding-3-small, text-embedding-3-large",
    )


class ListModelsInput(BaseModel):
    filter: Optional[str] = Field(
        default=None,
        description="필터 키워드 (예: 'gpt-4', 'o1'). 없으면 주요 모델 반환",
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

def _resolve_openai_client():
    """
    인증 방식을 자동 탐색하여 AsyncOpenAI 클라이언트를 반환합니다.

    우선순위:
      1. OPENAI_API_KEY   → API 키 모드 (sk-... 또는 proj-...)
      2. OPENAI_AUTH_TYPE=oauth + OPENAI_OAUTH_TOKEN → OAuth 모드
      3. 둘 다 없으면 None 반환 (호출자가 오류 처리)
    """
    from openai import AsyncOpenAI

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return AsyncOpenAI(api_key=api_key), "api_key"

    auth_type = os.environ.get("OPENAI_AUTH_TYPE", "").lower()
    if auth_type == "oauth":
        oauth_token = os.environ.get("OPENAI_OAUTH_TOKEN")
        if oauth_token:
            # OAuth 토큰도 Bearer 토큰으로 동일하게 사용
            return AsyncOpenAI(api_key=oauth_token), "oauth"
        # OAuth 모드지만 토큰 미주입 → 시스템이 나중에 주입할 수 있으므로 대기 후 재시도 안내
        return None, "oauth_token_missing"

    return None, "no_auth"


@mcp.tool(
    name="codex_generate",
    annotations={"readOnlyHint": False, "openWorldHint": True},
)
async def codex_generate(params: GenerateInput) -> str:
    """
    OpenAI 모델(GPT-4o, o1, o3 등)로 텍스트를 생성합니다.

    relay backed_by 예:
      backed_by: codex:gpt-4o
      backed_by: codex:gpt-4o-mini
      backed_by: codex:o3-mini

    인증 방식:
      API 키 모드  : OPENAI_API_KEY 환경변수 설정
      OAuth 모드   : OPENAI_AUTH_TYPE=oauth + OPENAI_OAUTH_TOKEN 자동 주입
    """
    try:
        from openai import AsyncOpenAI

        client, auth_mode = _resolve_openai_client()
        if client is None:
            if auth_mode == "oauth_token_missing":
                return (
                    "오류: OAuth 모드이지만 OPENAI_OAUTH_TOKEN 이 주입되지 않았습니다.\n"
                    "Claude Code 또는 시스템의 OAuth 연결 상태를 확인하세요."
                )
            return (
                "오류: OpenAI 인증 정보가 없습니다.\n"
                "  • API 키 방식: OPENAI_API_KEY 환경변수를 설정하세요.\n"
                "  • OAuth 방식: /relay:setup-keys 에서 OAuth 연결을 선택하세요."
            )

        # system + context(선택) 합성 → 항상 one-shot
        system_content = params.system
        if params.context:
            system_content = f"{params.system}\n\n## 배경 컨텍스트\n{params.context}"

        messages: list[dict] = [
            {"role": "system", "content": system_content},
            {"role": "user",   "content": params.prompt},
        ]

        kwargs: dict = {
            "model": params.model,
            "messages": messages,
            "max_tokens": params.max_tokens,
        }

        # o1/o3 계열은 temperature 미지원
        if not params.model.startswith(("o1", "o3")):
            kwargs["temperature"] = params.temperature

        if params.response_format == "json_object":
            kwargs["response_format"] = {"type": "json_object"}

        response = await client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    except ImportError:
        return "오류: openai 패키지가 설치되지 않았습니다.\npip install openai"
    except Exception as e:
        return f"OpenAI API 오류: {e}"


@mcp.tool(
    name="codex_review_code",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def codex_review_code(params: CodeReviewInput) -> str:
    """
    코드를 리뷰하고 개선점을 제안합니다.
    relay 팀의 코드 리뷰 전문가 역할에 적합합니다.
    """
    try:
        client, auth_mode = _resolve_openai_client()
        if client is None:
            return "오류: OpenAI 인증 정보가 없습니다. OPENAI_API_KEY 또는 OAuth 연결을 확인하세요."

        system_prompt = (
            f"당신은 {params.language} 전문 코드 리뷰어입니다. "
            f"다음 항목에 집중해서 리뷰하세요: {params.focus}. "
            "문제점, 개선 제안, 수정된 코드 예시를 포함해서 응답하세요."
        )

        response = await client.chat.completions.create(
            model=params.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"```{params.language}\n{params.code}\n```"},
            ],
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    except ImportError:
        return "오류: openai 패키지가 설치되지 않았습니다."
    except Exception as e:
        return f"코드 리뷰 오류: {e}"


@mcp.tool(
    name="codex_embed",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def codex_embed(params: EmbedInput) -> str:
    """
    텍스트를 OpenAI 임베딩 벡터로 변환합니다.
    """
    try:
        client, auth_mode = _resolve_openai_client()
        if client is None:
            return "오류: OpenAI 인증 정보가 없습니다. OPENAI_API_KEY 또는 OAuth 연결을 확인하세요."

        response = await client.embeddings.create(
            model=params.model,
            input=params.text,
        )
        values = response.data[0].embedding
        return f"임베딩 완료 (차원: {len(values)})\n{values[:8]}... (첫 8개 값)"

    except ImportError:
        return "오류: openai 패키지가 설치되지 않았습니다."
    except Exception as e:
        return f"임베딩 오류: {e}"


@mcp.tool(
    name="codex_list_models",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def codex_list_models(params: ListModelsInput) -> str:
    """
    사용 가능한 OpenAI 모델 목록을 반환합니다.
    """
    # 주요 모델 하드코딩 (API 호출 없이 빠르게 확인)
    known_models = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "o1",
        "o1-mini",
        "o3-mini",
        "text-embedding-3-small",
        "text-embedding-3-large",
    ]

    if params.filter:
        known_models = [m for m in known_models if params.filter.lower() in m.lower()]

    if not known_models:
        return "해당 조건의 모델이 없습니다."

    lines = ["사용 가능한 주요 OpenAI 모델:"]
    for m in known_models:
        lines.append(f"  - {m}")
    lines.append("\nbacked_by 형식: codex:{모델명}  예) codex:gpt-4o")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
