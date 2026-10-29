"""
적금 상품 추천 워크플로우 (Deposit Advisor Flow)

사용자가 업로드한 적금 상품 안내 PDF에서 docext로 상품 정보를 추출하고,
사용자 정보(나이, 목적, 선호 기간, 예산)를 수집하여 맞춤 적금 상품을 추천합니다.

워크플로우 순서:
  START
    → [1] PDF 업로드 + 적금 상품 정보 추출 (docext)
    → [2] 사용자 정보 수집 폼 (userflow)
    → [3] 상품 추천 생성 (prompt / LLM)
  END
"""

from pydantic import BaseModel, Field  # DocExtConfigField 등 내부에서 사용
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END, DataMap
from ibm_watsonx_orchestrate.flow_builder.types import (
    DocExtConfigField,
    DocumentProcessingCommonInput,
)


# ── 적금 상품 필드 정의 ────────────────────────────────────────────────────────

class DepositProductFields(BaseModel):
    """PDF 전체 텍스트를 하나의 필드로 추출 — 파싱 오류 방지"""

    full_text: DocExtConfigField = Field(
        default=DocExtConfigField(
            name="적금 상품 안내 전문",
            field_name="full_text",
            type="string",
            description=(
                "PDF에 기재된 모든 적금 상품(A/B/C)의 정보를 원문 그대로 추출합니다. "
                "상품명, 가입 연령, 금리, 납입 방식, 월 납입 한도, 가입 기간, "
                "특별 혜택, 만기 수령액 표를 포함한 전체 내용을 빠짐없이 포함하세요."
            ),
        )
    )


# ── 플로우 정의 ───────────────────────────────────────────────────────────────

@flow(
    name="deposit_advisor_flow",
    display_name="적금 상품 추천 워크플로우",
    description=(
        "적금 상품 안내 PDF를 업로드하면 상품 정보를 자동 추출하고, "
        "고객의 나이·저축 목적·선호 기간·예산을 수집하여 "
        "가장 적합한 적금 상품(A/B/C)을 추천합니다."
    ),
    input_schema=DocumentProcessingCommonInput,
    suppress_agent_summarization=True,
)
def build_deposit_advisor_flow(aflow: Flow) -> Flow:
    """
    플로우 단계:
      1. docext   — PDF 업로드 후 적금 상품 필드 추출 (layout 방식)
      2. userflow — 고객 나이·저축목적·선호기간·예산 폼 수집
      3. prompt   — 추출된 상품 정보 + 고객 정보 → LLM 추천 생성
    """

    # ── Step 1: docext — PDF에서 적금 상품 정보 추출 ────────────────────────
    extract_node, _ExtractedSchema = aflow.docext(
        name="extract_deposit_info",
        display_name="적금 상품 정보 추출",
        description=(
            "적금 상품 안내 PDF에서 상품명, 금리, 대상 연령, "
            "납입 방식, 혜택, 만기 수령액 표를 추출합니다."
        ),
        llm="watsonx/mistralai/mistral-small-3-1-24b-instruct-2503",
        fields=DepositProductFields(),
        field_extraction_method="classic",
    )

    # ── Step 2: userflow — 사용자 정보 수집 폼 ──────────────────────────────
    uf = aflow.userflow(name="collect_customer_info", display_name="고객 정보 입력")
    form = uf.form(
        name="customer_info_form",
        display_name="맞춤 적금 추천을 위한 고객 정보",
    )
    form.number_input_field(
        name="age",
        label="나이 (만 나이)",
        is_integer=True,
    )
    form.text_input_field(
        name="purpose",
        label="저축 목적 (예: 노후준비, 결혼자금, 여행비, 자녀교육)",
        required=True,
    )
    form.text_input_field(
        name="preferred_term",
        label="선호 가입 기간 (예: 12개월, 24개월, 36개월)",
        required=True,
    )
    form.number_input_field(
        name="monthly_budget",
        label="월 납입 가능 금액 (만 원)",
        is_integer=True,
        minimum=DataMap(),
        help_text="1만 원 이상 입력해 주세요.",
    )
    uf.edge(START, form)
    uf.edge(form, END)

    # ── Step 3: prompt — LLM 추천 생성 ─────────────────────────────────────
    recommend_node = aflow.prompt(
        name="recommend_product",
        display_name="맞춤 적금 상품 추천",
        system_prompt=(
            "당신은 친절한 금융 상담사입니다.\n"
            "아래 제공된 적금 상품 정보(PDF에서 추출)와 고객 정보만을 근거로 답변하세요.\n"
            "외부 지식이나 다른 금융 기관 상품 정보를 절대 사용하지 마세요.\n\n"
            "상품 선택 규칙 (반드시 이 순서로 적용):\n"
            "1. 가입 연령 조건을 충족하는 상품만 후보로 남깁니다.\n"
            "2. 후보 중 고객 선호 기간과 가장 가까운 기간 옵션을 찾습니다.\n"
            "3. 후보 상품 중 해당 월 납입 금액 기준 만기 수령액이 가장 높은 상품을 추천합니다.\n"
            "4. 선호 기간과 실제 추천 기간이 다를 경우 반드시 그 이유를 명시합니다.\n\n"
            "반드시 아래 형식으로만 답변하세요. JSON·코드블록 없이 작성하세요.\n\n"
            "🏦 **추천 상품: [상품명]**\n\n"
            "**추천 이유**\n"
            "[연령 조건, 금리·혜택, 만기 수령액 비교 근거를 구체적 수치로 2~3문장]\n\n"
            "**예상 만기 수령액**\n"
            "[고객 월 납입 금액 기준 수령액을 구체적 금액으로]\n\n"
            "**⚠️ 가입 전 유의사항**\n"
            "- [유의사항 1]\n"
            "- [유의사항 2]\n"
            "- [유의사항 3]\n\n"
            "💡 더 궁금한 점이 있으시면 편하게 물어보세요!\n\n"
            "투자 결과를 보장하는 표현은 절대 사용하지 마세요."
        ),
        user_prompt=[
            "=== 적금 상품 정보 (업로드된 PDF 추출) ===\n{product_data}\n\n"
            "=== 고객 정보 ===\n{customer_info}\n\n"
            "위 정보만을 근거로, 조건에 맞으면서 만기 수령액이 가장 높은 적금 상품을 추천해 주세요."
        ],
        llm="groq/openai/gpt-oss-120b",
    )
    recommend_node.map_input("product_data",  'flow["extract_deposit_info"].output')
    recommend_node.map_input("customer_info", 'flow["collect_customer_info"].output')

    # flow 최종 output → recommend_product의 output으로 매핑
    aflow.map_flow_output_with_variable("output", "recommend_product.output")

    # ── 엣지 배선 ─────────────────────────────────────────────────────────────
    aflow.sequence(START, extract_node, uf, recommend_node, END)

    return aflow
