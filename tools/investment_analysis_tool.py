"""
투자 성향 분석 도구 (Investment Profile Analysis Tool)
투자자의 성향을 분석하고 적합한 포트폴리오를 추천합니다.
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from pydantic import BaseModel, Field
from typing import Optional


class InvestmentProfileResult(BaseModel):
    investor_type: str = Field(description="투자자 유형 (안정형/안정추구형/위험중립형/적극투자형/공격투자형)")
    risk_score: int = Field(description="위험 성향 점수 (1~100)")
    description: str = Field(description="투자자 유형 설명")
    recommended_portfolio: str = Field(description="추천 포트폴리오 구성")
    expected_return_min: float = Field(description="기대 수익률 최솟값 (%)")
    expected_return_max: float = Field(description="기대 수익률 최댓값 (%)")
    suitable_products: list = Field(description="적합한 금융 상품 목록")
    caution: str = Field(description="주의 사항")


class RegulatoryCheckResult(BaseModel):
    is_compliant: bool = Field(description="규정 준수 여부")
    applicable_regulations: list = Field(description="적용 가능한 규정 목록")
    action_required: str = Field(description="필요한 조치")
    summary: str = Field(description="규정 준수 요약")


@tool(permission=ToolPermission.READ_ONLY)
def analyze_investment_profile(
    investment_goal: str,
    investment_horizon_years: int,
    risk_tolerance: str,
    monthly_income_range: str,
    existing_assets_range: str,
) -> InvestmentProfileResult:
    """투자자의 목표, 투자 기간, 위험 허용도를 기반으로 투자 성향을 분석하고 포트폴리오를 추천합니다.

    Args:
        investment_goal (str): 투자 목표 (예: 노후준비, 주택자금, 자녀교육, 단기수익, 자산증식).
        investment_horizon_years (int): 투자 기간 (년 단위).
        risk_tolerance (str): 위험 허용도 (낮음/중간/높음).
        monthly_income_range (str): 월 소득 범위 (예: 200-300만원, 300-500만원, 500만원이상).
        existing_assets_range (str): 보유 자산 범위 (예: 1억미만, 1-3억, 3-5억, 5억이상).
    Returns:
        InvestmentProfileResult: 투자자 유형, 추천 포트폴리오, 적합 상품 목록.
    """
    risk_score = 50

    if risk_tolerance == "낮음":
        risk_score -= 20
    elif risk_tolerance == "높음":
        risk_score += 20

    if investment_horizon_years >= 10:
        risk_score += 15
    elif investment_horizon_years >= 5:
        risk_score += 5
    elif investment_horizon_years <= 2:
        risk_score -= 15

    if investment_goal in ["노후준비", "자녀교육"]:
        risk_score += 5
    elif investment_goal == "단기수익":
        risk_score -= 10
    elif investment_goal == "자산증식":
        risk_score += 10

    if existing_assets_range == "5억이상":
        risk_score += 10
    elif existing_assets_range == "1억미만":
        risk_score -= 5

    risk_score = max(10, min(95, risk_score))

    if risk_score <= 25:
        investor_type = "안정형"
        description = "원금 보존을 최우선으로 하며 안정적인 수익을 추구합니다."
        portfolio = "예금 50%, 국채/채권형 펀드 40%, 현금성 자산 10%"
        ret_min, ret_max = 2.0, 4.0
        suitable = ["보통예금", "정기예금", "자유적금", "채권형 펀드", "국채 ETF"]
        caution = "물가 상승률보다 낮은 실질 수익률에 유의하세요."
    elif risk_score <= 45:
        investor_type = "안정추구형"
        description = "원금 손실 가능성은 최소화하면서 예금보다 높은 수익을 원합니다."
        portfolio = "채권 70% (국채 40% + 회사채 30%) + 주식형 펀드 30%"
        ret_min, ret_max = 3.0, 6.0
        suitable = ["정기예금", "채권형 펀드", "혼합형 펀드", "배당주 ETF"]
        caution = "채권 금리 변동에 따른 평가손실 가능성을 인지하세요."
    elif risk_score <= 65:
        investor_type = "위험중립형"
        description = "적정 수준의 위험을 감수하고 중장기 자산 증대를 추구합니다."
        portfolio = "주식형 펀드 50% + 채권형 펀드 35% + 현금 15%"
        ret_min, ret_max = 5.0, 9.0
        suitable = ["국내주식형 펀드", "해외주식형 펀드", "KOSPI 200 ETF", "S&P 500 ETF", "혼합형 펀드"]
        caution = "단기 시장 변동성을 감내할 수 있는 여유자금으로 투자하세요."
    elif risk_score <= 80:
        investor_type = "적극투자형"
        description = "높은 수익을 위해 상당한 원금 손실 위험을 감수할 의향이 있습니다."
        portfolio = "주식형 펀드 70% + 채권형 펀드 20% + 대안투자 10%"
        ret_min, ret_max = 7.0, 13.0
        suitable = ["국내주식형 펀드", "해외주식형 펀드", "섹터 ETF", "리츠(REITs)"]
        caution = "시장 하락 시 30% 이상 손실 가능성을 염두에 두세요."
    else:
        investor_type = "공격투자형"
        description = "최대 수익을 위해 높은 위험을 기꺼이 감수합니다."
        portfolio = "주식형 펀드 80% + 대안투자 15% + 현금 5%"
        ret_min, ret_max = 10.0, 25.0
        suitable = ["성장주 펀드", "신흥국 펀드", "섹터 집중 ETF", "사모펀드(PE)"]
        caution = "포트폴리오 가치가 50% 이상 하락할 수 있습니다. 분산 투자를 반드시 지키세요."

    return InvestmentProfileResult(
        investor_type=investor_type,
        risk_score=risk_score,
        description=description,
        recommended_portfolio=portfolio,
        expected_return_min=ret_min,
        expected_return_max=ret_max,
        suitable_products=suitable,
        caution=caution,
    )


@tool(permission=ToolPermission.READ_ONLY)
def check_regulatory_compliance(
    product_type: str,
    transaction_amount: int,
    investor_type: str,
) -> RegulatoryCheckResult:
    """금융 거래의 규정 준수 여부를 확인하고 필요한 조치를 안내합니다.

    Args:
        product_type (str): 금융 상품 유형 (예금, 대출, 펀드, 파생상품, 외환).
        transaction_amount (int): 거래 금액 (원 단위).
        investor_type (str): 투자자 유형 (안정형, 안정추구형, 위험중립형, 적극투자형, 공격투자형).
    Returns:
        RegulatoryCheckResult: 규정 준수 여부, 적용 법규, 필요 조치.
    """
    regulations = []
    actions = []
    is_compliant = True

    if product_type in ["펀드", "파생상품", "ETF"]:
        regulations.append("자본시장법 - 적합성 원칙 (투자자 성향 적합 여부 확인)")
        regulations.append("금융소비자보호법 - 설명 의무")
        if investor_type == "안정형" and product_type == "파생상품":
            is_compliant = False
            actions.append("안정형 투자자에게는 파생상품 권유 불가 — 투자 성향 재확인 필요")

    if transaction_amount >= 10000000:
        regulations.append("자금세탁방지법 (AML) — 고액현금거래보고(CTR) 대상 (1일 1,000만 원 이상)")
        actions.append("자금 출처 확인 및 KoFIU 보고 절차 진행")

    if transaction_amount >= 100000000:
        regulations.append("대규모 거래 내부 결재 기준 — 1억 원 이상 거래 담당 임원 승인 필요")
        actions.append("내부 결재 시스템을 통해 책임자 승인 후 처리")

    if product_type == "예금":
        regulations.append("예금자보호법 — 1인당 5,000만 원까지 예금보험공사 보호")
        if transaction_amount > 50000000:
            actions.append("5,000만 원 초과분은 예금자 보호 미적용 — 고객에게 안내 필요")

    if product_type == "대출":
        regulations.append("은행법 및 금융소비자보호법 — DSR 40% 이하 적용")
        regulations.append("은행업감독규정 — LTV/DTI 규제 적용")

    if product_type == "외환" and transaction_amount >= 50000000:
        regulations.append("외국환거래법 — 미화 10,000달러 상당 초과 해외 송금 신고 의무")
        actions.append("외국환신고서 작성 및 제출 필요")

    if not regulations:
        regulations.append("특별한 규제 요건 없음 — 일반 금융거래 기준 적용")

    action_required = "; ".join(actions) if actions else "추가 조치 불필요 — 표준 절차에 따라 처리"
    summary = (
        f"{'규정 준수 가능' if is_compliant else '규정 위반 — 즉시 수정 필요'}: "
        f"{product_type} 거래 {transaction_amount:,}원, 투자자 유형 '{investor_type}'. "
        f"적용 규정 {len(regulations)}건 확인됨."
    )

    return RegulatoryCheckResult(
        is_compliant=is_compliant,
        applicable_regulations=regulations,
        action_required=action_required,
        summary=summary,
    )
