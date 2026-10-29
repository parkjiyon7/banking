"""
금융 상품 조회 도구 (Financial Product Lookup Tool)
금융 상품의 금리, 한도, 조건 등의 정보를 조회합니다.
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from pydantic import BaseModel, Field
from typing import Optional


class ProductInfo(BaseModel):
    product_name: str = Field(description="금융 상품명")
    product_type: str = Field(description="상품 유형 (예금, 적금, 대출, 투자)")
    interest_rate_min: float = Field(description="최소 금리 (%)")
    interest_rate_max: float = Field(description="최대 금리 (%)")
    min_amount: int = Field(description="최소 가입 금액 (원)")
    max_amount: int = Field(description="최대 가입/대출 금액 (원)")
    term_months_min: int = Field(description="최소 기간 (개월)")
    term_months_max: int = Field(description="최대 기간 (개월)")
    description: str = Field(description="상품 설명")
    eligibility: str = Field(description="가입 자격 조건")


PRODUCT_DATABASE = {
    "보통예금": ProductInfo(
        product_name="보통예금",
        product_type="예금",
        interest_rate_min=0.1,
        interest_rate_max=0.5,
        min_amount=0,
        max_amount=500000000,
        term_months_min=0,
        term_months_max=0,
        description="입출금이 자유로운 기본 예금 상품. 유동성이 높으며 언제든지 출금 가능.",
        eligibility="개인 및 법인 누구나 가입 가능",
    ),
    "정기예금": ProductInfo(
        product_name="정기예금",
        product_type="예금",
        interest_rate_min=3.5,
        interest_rate_max=4.8,
        min_amount=1000000,
        max_amount=1000000000,
        term_months_min=1,
        term_months_max=36,
        description="약정 기간 동안 자금을 예치하고 만기 시 원금과 이자를 수령. 예금자 보호 5,000만원.",
        eligibility="개인 및 법인 누구나 가입 가능",
    ),
    "자유적금": ProductInfo(
        product_name="자유적금",
        product_type="적금",
        interest_rate_min=3.8,
        interest_rate_max=4.5,
        min_amount=10000,
        max_amount=3000000,
        term_months_min=6,
        term_months_max=36,
        description="매월 자유롭게 납입 금액을 설정할 수 있는 적금 상품.",
        eligibility="개인 가입 가능",
    ),
    "주택담보대출": ProductInfo(
        product_name="주택담보대출",
        product_type="대출",
        interest_rate_min=4.0,
        interest_rate_max=5.8,
        min_amount=10000000,
        max_amount=1000000000,
        term_months_min=120,
        term_months_max=480,
        description="주택을 담보로 제공하는 대출. LTV 70% 이내. DSR 40% 이하 적용.",
        eligibility="주택 소유자, 신용점수 650점 이상",
    ),
    "신용대출": ProductInfo(
        product_name="신용대출",
        product_type="대출",
        interest_rate_min=5.5,
        interest_rate_max=12.0,
        min_amount=1000000,
        max_amount=100000000,
        term_months_min=12,
        term_months_max=60,
        description="담보 없이 신용만으로 대출. 연소득 최대 1.5배 한도.",
        eligibility="신용점수 700점 이상 (KCB 기준), 재직기간 1년 이상",
    ),
}


@tool(permission=ToolPermission.READ_ONLY)
def get_financial_product_info(product_name: str) -> ProductInfo:
    """특정 금융 상품의 상세 정보를 조회합니다.

    Args:
        product_name (str): 조회할 금융 상품명 (예: 보통예금, 정기예금, 자유적금, 주택담보대출, 신용대출).
    Returns:
        ProductInfo: 금융 상품의 금리, 한도, 기간 등 상세 정보.
    """
    if product_name in PRODUCT_DATABASE:
        return PRODUCT_DATABASE[product_name]
    for key, product in PRODUCT_DATABASE.items():
        if product_name.lower() in key.lower() or key.lower() in product_name.lower():
            return product
    return ProductInfo(
        product_name=product_name,
        product_type="알 수 없음",
        interest_rate_min=0.0,
        interest_rate_max=0.0,
        min_amount=0,
        max_amount=0,
        term_months_min=0,
        term_months_max=0,
        description=f"'{product_name}' 상품을 찾을 수 없습니다. 지식 베이스를 통해 검색하시기 바랍니다.",
        eligibility="해당 없음",
    )


class ProductListResult(BaseModel):
    products: list = Field(description="금융 상품 목록")
    total_count: int = Field(description="총 상품 수")


@tool(permission=ToolPermission.READ_ONLY)
def list_financial_products(product_type: Optional[str] = None) -> ProductListResult:
    """가입 가능한 금융 상품 목록을 조회합니다.

    Args:
        product_type (str): 상품 유형 필터 (예금, 적금, 대출, 투자). None이면 전체 조회.
    Returns:
        ProductListResult: 금융 상품 목록과 총 개수.
    """
    if product_type:
        filtered = [
            {"이름": p.product_name, "유형": p.product_type, "금리": f"{p.interest_rate_min}~{p.interest_rate_max}%"}
            for p in PRODUCT_DATABASE.values()
            if p.product_type == product_type
        ]
    else:
        filtered = [
            {"이름": p.product_name, "유형": p.product_type, "금리": f"{p.interest_rate_min}~{p.interest_rate_max}%"}
            for p in PRODUCT_DATABASE.values()
        ]
    return ProductListResult(products=filtered, total_count=len(filtered))
