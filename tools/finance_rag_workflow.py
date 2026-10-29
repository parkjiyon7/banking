"""
금융 RAG 워크플로우 (Finance RAG Workflow)
사용자의 금융 질의를 분류하고 지식 베이스 검색, 데이터 조회, 분석을 통해
종합적인 금융 답변을 생성하는 워크플로우입니다.
"""

from pydantic import BaseModel, Field
from ibm_watsonx_orchestrate.flow_builder.flows import Flow, flow, START, END

from tools.financial_product_tool import get_financial_product_info, list_financial_products
from tools.market_data_tool import get_market_index, get_exchange_rate, get_interest_rate
from tools.investment_analysis_tool import analyze_investment_profile, check_regulatory_compliance


# ── 입력/출력 스키마 ────────────────────────────────────────────────────────────

class FinanceQueryInput(BaseModel):
    query: str = Field(description="사용자의 금융 관련 질문")
    query_category: str = Field(
        description=(
            "질문 카테고리: 'product' (상품 문의), 'market' (시장/환율/금리 조회), "
            "'investment' (투자 성향 분석), 'compliance' (규정 준수 확인), 'general' (일반 금융 정보)"
        )
    )


class FinanceQueryOutput(BaseModel):
    answer: str = Field(description="사용자 질문에 대한 종합 답변")
    data_source: str = Field(description="답변 근거 데이터 출처")
    category: str = Field(description="처리된 질문 카테고리")
    follow_up_suggestions: list = Field(description="추가 질문 제안 목록")


class ClassificationOutput(BaseModel):
    category: str = Field(description="분류된 카테고리")
    confidence: str = Field(description="분류 신뢰도")
    extracted_params: str = Field(description="추출된 주요 파라미터 (JSON 형식 문자열)")


class FinalAnswer(BaseModel):
    answer: str = Field(description="최종 답변")
    data_source: str = Field(description="데이터 출처")
    follow_up_suggestions: list = Field(description="추가 질문 제안 목록")


# ── 플로우 정의 ─────────────────────────────────────────────────────────────────

@flow(
    name="finance_rag_workflow",
    display_name="금융 RAG 워크플로우",
    description=(
        "사용자의 금융 질의를 카테고리별로 분류하여 "
        "지식 베이스 RAG 검색과 전문 도구를 결합해 "
        "정확하고 신뢰할 수 있는 금융 정보를 제공합니다."
    ),
    input_schema=FinanceQueryInput,
    output_schema=FinanceQueryOutput,
    suppress_agent_summarization=False,
)
def build_finance_rag_workflow(aflow: Flow) -> Flow:
    """
    워크플로우 구조:
      START
        → 질의 분류 (LLM prompt)
        → 카테고리 라우터 (conditions)
            ├─ product   → 상품 정보 조회 → 상품 답변 생성
            ├─ market    → 시장 데이터 조회 → 시장 답변 생성
            ├─ investment→ 투자 성향 분석 → 투자 답변 생성
            ├─ compliance→ 규정 준수 확인 → 규정 답변 생성
            └─ general   → KB 기반 일반 답변 생성
        → 응답 통합 (script)
      END
    """

    # ── 1단계: 질의 분류 ─────────────────────────────────────────────────────────
    classify = aflow.prompt(
        name="classify_query",
        display_name="금융 질의 분류",
        system_prompt=(
            "당신은 금융 전문 분류 시스템입니다. 사용자의 질문을 아래 5가지 카테고리 중 하나로 분류하세요.\n\n"
            "카테고리:\n"
            "- product: 예금, 적금, 대출, 투자 상품의 금리/한도/조건 문의\n"
            "- market: 주가 지수, 환율, 기준금리 등 시장 데이터 조회\n"
            "- investment: 투자 성향 분석, 포트폴리오 추천\n"
            "- compliance: 금융 규정, 법규, 준수 의무 확인\n"
            "- general: 위 카테고리에 해당하지 않는 일반 금융 정보\n\n"
            "응답 형식(JSON):\n"
            "{\n"
            '  "category": "<분류 카테고리>",\n'
            '  "confidence": "high/medium/low",\n'
            '  "extracted_params": "<추출된 핵심 파라미터 설명>"\n'
            "}"
        ),
        user_prompt=["사용자 질문: {query}\n제공된 카테고리: {query_category}"],
        llm="groq/openai/gpt-oss-120b",
        output_schema=ClassificationOutput,
    )
    classify.map_input("query", "flow.input.query")
    classify.map_input("query_category", "flow.input.query_category")

    # ── 2단계: 상품 정보 조회 노드 ─────────────────────────────────────────────
    product_lookup = aflow.tool(get_financial_product_info)
    product_lookup.map_input("product_name", "flow.input.query")

    # ── 3단계: 시장 데이터 조회 노드 ───────────────────────────────────────────
    market_lookup = aflow.tool(get_market_index)
    market_lookup.map_input("index_name", "flow.input.query")

    # ── 4단계: 환율 조회 노드 ─────────────────────────────────────────────────
    fx_lookup = aflow.tool(get_exchange_rate)
    fx_lookup.map_input("currency_pair", "flow.input.query")

    # ── 5단계: 금리 조회 노드 ──────────────────────────────────────────────────
    rate_lookup = aflow.tool(get_interest_rate)
    rate_lookup.map_input("rate_type", "flow.input.query")

    # ── 6단계: 상품 목록 조회 (일반 문의 fallback) ────────────────────────────
    product_list = aflow.tool(list_financial_products)

    # ── 7단계: 상품 답변 생성 ────────────────────────────────────────────────
    product_answer = aflow.prompt(
        name="generate_product_answer",
        display_name="상품 정보 답변 생성",
        system_prompt=(
            "당신은 친절하고 전문적인 금융 상품 전문가입니다. "
            "고객의 금융 상품 문의에 대해 정확하고 이해하기 쉬운 답변을 제공하세요. "
            "금리, 한도, 기간, 자격 조건 등 핵심 정보를 명확하게 전달하고, "
            "고객이 이해하기 어려운 금융 용어는 쉽게 설명해 주세요. "
            "답변 마지막에 추가로 궁금할 만한 질문 2~3개를 제안하세요."
        ),
        user_prompt=[
            "고객 질문: {query}\n\n"
            "조회된 상품 정보:\n{product_info}\n\n"
            "위 정보를 바탕으로 고객에게 도움이 되는 상세한 답변을 작성하세요."
        ],
        llm="groq/openai/gpt-oss-120b",
        output_schema=FinalAnswer,
    )
    product_answer.map_input("query", "flow.input.query")
    product_answer.map_input("product_info", "flow.get_financial_product_info.output")

    # ── 8단계: 시장 답변 생성 ────────────────────────────────────────────────
    market_answer = aflow.prompt(
        name="generate_market_answer",
        display_name="시장 데이터 답변 생성",
        system_prompt=(
            "당신은 금융 시장 분석 전문가입니다. "
            "주가 지수, 환율, 금리 등의 시장 데이터를 바탕으로 "
            "현재 시장 상황을 명확하게 설명하고 투자 참고 정보를 제공하세요. "
            "데이터를 해석하여 일반 투자자가 이해할 수 있도록 설명하고, "
            "투자 결정은 개인의 판단에 따라야 함을 항상 안내하세요."
        ),
        user_prompt=[
            "고객 질문: {query}\n\n"
            "시장 지수 데이터:\n{market_data}\n"
            "환율 데이터:\n{fx_data}\n"
            "금리 데이터:\n{rate_data}\n\n"
            "위 데이터를 바탕으로 시장 현황을 설명하는 답변을 작성하세요."
        ],
        llm="groq/openai/gpt-oss-120b",
        output_schema=FinalAnswer,
    )
    market_answer.map_input("query", "flow.input.query")
    market_answer.map_input("market_data", "flow.get_market_index.output")
    market_answer.map_input("fx_data", "flow.get_exchange_rate.output")
    market_answer.map_input("rate_data", "flow.get_interest_rate.output")

    # ── 9단계: 일반 금융 정보 답변 생성 ─────────────────────────────────────
    general_answer = aflow.prompt(
        name="generate_general_answer",
        display_name="일반 금융 정보 답변 생성",
        system_prompt=(
            "당신은 금융 전문 상담사입니다. "
            "금융 규정, 투자 전략, 리스크 관리, 시장 전망 등에 대한 전문적 지식을 바탕으로 "
            "고객의 금융 관련 질문에 정확하고 도움이 되는 답변을 제공하세요. "
            "지식 베이스에 기반한 정보를 활용하되, 개인화된 금융 조언보다는 "
            "일반적인 금융 정보를 제공하는 데 집중하세요. "
            "답변 마지막에 추가로 알아볼 만한 주제 2~3가지를 제안하세요."
        ),
        user_prompt=[
            "고객 질문: {query}\n\n"
            "제공 가능한 금융 상품 목록:\n{product_list}\n\n"
            "고객의 질문에 대해 지식 베이스 정보를 바탕으로 명확하고 유용한 답변을 제공하세요."
        ],
        llm="groq/openai/gpt-oss-120b",
        output_schema=FinalAnswer,
    )
    general_answer.map_input("query", "flow.input.query")
    general_answer.map_input("product_list", "flow.list_financial_products.output")

    # ── 10단계: 카테고리 라우터 ────────────────────────────────────────────────
    router = aflow.conditions(name="category_router")
    router.condition(
        expression="flow.classify_query.output.category == 'product'",
        to_node=product_lookup,
    )
    router.condition(
        expression="flow.classify_query.output.category == 'market'",
        to_node=market_lookup,
    )
    router.condition(
        expression="flow.classify_query.output.category == 'compliance'",
        to_node=product_list,
    )
    router.condition(
        expression="flow.classify_query.output.category == 'investment'",
        to_node=product_list,
    )
    router.condition(default=True, to_node=product_list)

    # ── 11단계: 통합 응답 스크립트 ──────────────────────────────────────────────
    consolidate = aflow.script(
        name="consolidate_output",
        script=(
            "self.output.answer = ('답변을 생성하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.');"
            "self.output.data_source = '금융 지식 베이스 + 실시간 시장 데이터';"
            "self.output.category = flow.classify_query.output.category;"
            "self.output.follow_up_suggestions = ['금융 상품에 대해 더 알고 싶으신가요?', '시장 현황이 궁금하신가요?', '투자 성향 분석을 원하시나요?']"
        ),
        output_schema=FinanceQueryOutput,
    )

    # ── 엣지 배선 ────────────────────────────────────────────────────────────────
    # 공통 흐름: START → 분류 → 라우터
    aflow.sequence(START, classify, router)

    # 상품 경로: product_lookup → product_answer → consolidate
    aflow.sequence(product_lookup, product_answer, consolidate)

    # 시장 경로: market_lookup → fx_lookup → rate_lookup → market_answer → consolidate
    aflow.sequence(market_lookup, fx_lookup, rate_lookup, market_answer, consolidate)

    # 일반/규정/투자 경로: product_list → general_answer → consolidate
    aflow.sequence(product_list, general_answer, consolidate)

    aflow.edge(consolidate, END)

    return aflow
