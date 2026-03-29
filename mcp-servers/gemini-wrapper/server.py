# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "mcp[cli]>=1.0.0",
#   "google-generativeai>=0.8.0",
#   "pydantic>=2.0.0",
# ]
# ///
"""
gemini_mcp — Google Gemini API wrapper for Claude Code / relay plugin

실행 방법:
  uv run server.py          # 의존성 자동 설치 후 실행
  uv run --python 3.11 server.py  # Python 버전 지정
"""

import os
from typing import Optional
from pydantic import BaseModel, Field
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("gemini_mcp")


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class GenerateInput(BaseModel):
    prompt: str = Field(..., description="현재 요청. 작업 지시문을 명확하게 작성합니다.")
    model: str = Field(
        default="gemini-2.5-flash",
        description="사용할 Gemini 모델. 예: gemini-2.5-flash, gemini-2.5-pro",
    )
    system: Optional[str] = Field(
        default=None,
        description="역할·제약·출력 형식 등 정적 지침",
    )
    context: Optional[str] = Field(
        default=None,
        description=(
            "이전 작업 결과·배경 정보의 요약 (선택). "
            "raw 대화 기록 대신 호출자(Claude Code)가 직접 압축한 컨텍스트를 전달합니다. "
            "system 뒤에 붙어 최종 시스템 인스트럭션을 구성합니다. "
            "예: '이전에 작성한 SNS 초안: [요약]. 브랜드 톤: 캐주얼'"
        ),
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="생성 다양성 조절 (0.0~2.0)",
    )
    max_output_tokens: int = Field(
        default=8192,
        ge=1,
        le=65536,
        description="최대 출력 토큰 수",
    )


class EmbedInput(BaseModel):
    text: str = Field(..., description="임베딩할 텍스트")
    model: str = Field(
        default="text-embedding-004",
        description="임베딩 모델. 예: text-embedding-004",
    )


class ListModelsInput(BaseModel):
    filter: Optional[str] = Field(
        default=None,
        description="필터 키워드 (예: 'gemini-2', 'flash'). 없으면 전체 반환",
    )


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(
    name="gemini_generate",
    annotations={"readOnlyHint": False, "openWorldHint": True},
)
async def gemini_generate(params: GenerateInput) -> str:
    """
    Gemini 모델로 텍스트를 생성합니다.

    relay backed_by 예:
      backed_by: gemini:gemini-2.5-flash
      backed_by: gemini:gemini-2.5-pro
    """
    try:
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다."

        genai.configure(api_key=api_key)

        generation_config = genai.GenerationConfig(
            temperature=params.temperature,
            max_output_tokens=params.max_output_tokens,
        )

        # context가 있으면 system instruction에 합성
        system_instruction = params.system or ""
        if params.context:
            system_instruction = (
                f"{system_instruction}\n\n## 배경 컨텍스트\n{params.context}"
            ).strip()

        model = genai.GenerativeModel(
            model_name=params.model,
            generation_config=generation_config,
            system_instruction=system_instruction or None,
        )

        # 항상 one-shot — 컨텍스트는 호출자(Claude Code)가 압축해서 전달
        response = model.generate_content(params.prompt)

        return response.text

    except ImportError:
        return "오류: google-generativeai 패키지가 설치되지 않았습니다.\npip install google-generativeai"
    except Exception as e:
        return f"Gemini API 오류: {e}"


@mcp.tool(
    name="gemini_embed",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def gemini_embed(params: EmbedInput) -> str:
    """
    텍스트를 Gemini 임베딩 벡터로 변환합니다.
    유사도 검색, 문서 클러스터링 등에 활용합니다.
    """
    try:
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다."

        genai.configure(api_key=api_key)
        result = genai.embed_content(
            model=params.model,
            content=params.text,
        )
        values = result["embedding"]
        return f"임베딩 완료 (차원: {len(values)})\n{values[:8]}... (첫 8개 값)"

    except ImportError:
        return "오류: google-generativeai 패키지가 설치되지 않았습니다."
    except Exception as e:
        return f"Gemini Embed 오류: {e}"


@mcp.tool(
    name="gemini_list_models",
    annotations={"readOnlyHint": True, "openWorldHint": True},
)
async def gemini_list_models(params: ListModelsInput) -> str:
    """
    사용 가능한 Gemini 모델 목록을 반환합니다.
    backed_by 값 지정 시 모델명 확인에 활용합니다.
    """
    try:
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            return "오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다."

        genai.configure(api_key=api_key)
        models = [
            m.name for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]

        if params.filter:
            models = [m for m in models if params.filter.lower() in m.lower()]

        return "\n".join(models) if models else "해당 조건의 모델이 없습니다."

    except ImportError:
        return "오류: google-generativeai 패키지가 설치되지 않았습니다."
    except Exception as e:
        return f"모델 목록 오류: {e}"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
