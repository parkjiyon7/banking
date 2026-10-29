"""
시장 데이터 조회 도구 (Market Data Tool)
주요 금융 지표, 환율, 금리 등 시장 데이터를 조회합니다.
"""

from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from pydantic import BaseModel, Field
from typing import Optional


class MarketIndexData(BaseModel):
    index_name: str = Field(description="지수 이름")
    current_value: float = Field(description="현재 지수 값")
    change_pct: float = Field(description="전일 대비 변동률 (%)")
    ytd_change_pct: float = Field(description="연초 대비 변동률 (%)")
    market_status: str = Field(description="시장 상태 (상승/하락/보합)")


class ExchangeRateData(BaseModel):
    base_currency: str = Field(description="기준 통화")
    target_currency: str = Field(description="대상 통화")
    rate: float = Field(description="환율")
    change_pct: float = Field(description="전일 대비 변동률 (%)")
    high_52w: float = Field(description="52주 최고 환율")
    low_52w: float = Field(description="52주 최저 환율")


class InterestRateData(BaseModel):
    rate_type: str = Field(description="금리 유형")
    current_rate: float = Field(description="현재 금리 (%)")
    previous_rate: float = Field(description="이전 금리 (%)")
    change_date: str = Field(description="최근 변경일")
    next_meeting_date: str = Field(description="다음 금통위/FOMC 일정")
    outlook: str = Field(description="금리 전망")


MARKET_INDICES = {
    "KOSPI": MarketIndexData(
        index_name="KOSPI (코스피)",
        current_value=2756.34,
        change_pct=0.82,
        ytd_change_pct=4.21,
        market_status="상승",
    ),
    "KOSDAQ": MarketIndexData(
        index_name="KOSDAQ (코스닥)",
        current_value=872.45,
        change_pct=-0.31,
        ytd_change_pct=-2.15,
        market_status="하락",
    ),
    "S&P500": MarketIndexData(
        index_name="S&P 500",
        current_value=5243.77,
        change_pct=0.57,
        ytd_change_pct=11.34,
        market_status="상승",
    ),
    "NASDAQ": MarketIndexData(
        index_name="NASDAQ Composite",
        current_value=16421.28,
        change_pct=0.93,
        ytd_change_pct=9.87,
        market_status="상승",
    ),
    "니케이": MarketIndexData(
        index_name="일본 니케이 225",
        current_value=38405.66,
        change_pct=1.12,
        ytd_change_pct=18.43,
        market_status="상승",
    ),
}

EXCHANGE_RATES = {
    "USD/KRW": ExchangeRateData(
        base_currency="USD",
        target_currency="KRW",
        rate=1331.50,
        change_pct=-0.18,
        high_52w=1380.00,
        low_52w=1285.00,
    ),
    "EUR/KRW": ExchangeRateData(
        base_currency="EUR",
        target_currency="KRW",
        rate=1437.20,
        change_pct=0.05,
        high_52w=1495.00,
        low_52w=1380.00,
    ),
    "JPY/KRW": ExchangeRateData(
        base_currency="JPY",
        target_currency="KRW",
        rate=8.82,
        change_pct=-0.42,
        high_52w=9.45,
        low_52w=8.50,
    ),
}

INTEREST_RATES = {
    "한국은행 기준금리": InterestRateData(
        rate_type="한국은행 기준금리",
        current_rate=3.50,
        previous_rate=3.50,
        change_date="2024-01-11",
        next_meeting_date="2024-05-23",
        outlook="2024년 하반기 1~2회 인하 가능성. 가계부채 및 물가 동향에 따라 결정.",
    ),
    "미국 연방기금금리": InterestRateData(
        rate_type="미국 연방기금금리 (Fed Funds Rate)",
        current_rate=5.375,
        previous_rate=5.375,
        change_date="2023-07-26",
        next_meeting_date="2024-05-01",
        outlook="2024년 하반기 1~2회 인하 전망. 인플레이션 둔화 확인 필요.",
    ),
    "코픽스": InterestRateData(
        rate_type="COFIX (코픽스, 신규취급액 기준)",
        current_rate=3.72,
        previous_rate=3.81,
        change_date="2024-03-15",
        next_meeting_date="2024-04-15",
        outlook="기준금리 동결 기조 유지, 당분간 3.5~4.0% 수준 유지 전망.",
    ),
}


@tool(permission=ToolPermission.READ_ONLY)
def get_market_index(index_name: str) -> MarketIndexData:
    """주요 주가 지수 현황을 조회합니다.

    Args:
        index_name (str): 조회할 지수명 (KOSPI, KOSDAQ, S&P500, NASDAQ, 니케이 중 하나).
    Returns:
        MarketIndexData: 현재 지수값, 등락률, 연초 대비 수익률 등 시장 지수 정보.
    """
    for key, data in MARKET_INDICES.items():
        if index_name.upper() in key.upper() or key.upper() in index_name.upper():
            return data
    return MarketIndexData(
        index_name=index_name,
        current_value=0.0,
        change_pct=0.0,
        ytd_change_pct=0.0,
        market_status=f"'{index_name}' 지수를 찾을 수 없습니다. KOSPI, KOSDAQ, S&P500, NASDAQ, 니케이 중 선택하세요.",
    )


@tool(permission=ToolPermission.READ_ONLY)
def get_exchange_rate(currency_pair: str) -> ExchangeRateData:
    """주요 통화쌍의 환율 정보를 조회합니다.

    Args:
        currency_pair (str): 통화쌍 (USD/KRW, EUR/KRW, JPY/KRW 중 하나).
    Returns:
        ExchangeRateData: 현재 환율, 등락률, 52주 최고/최저 환율 정보.
    """
    normalized = currency_pair.upper().replace(" ", "")
    for key, data in EXCHANGE_RATES.items():
        if normalized == key or normalized in key or key in normalized:
            return data
    return ExchangeRateData(
        base_currency=currency_pair.split("/")[0] if "/" in currency_pair else "N/A",
        target_currency=currency_pair.split("/")[1] if "/" in currency_pair else "N/A",
        rate=0.0,
        change_pct=0.0,
        high_52w=0.0,
        low_52w=0.0,
    )


@tool(permission=ToolPermission.READ_ONLY)
def get_interest_rate(rate_type: str) -> InterestRateData:
    """주요 기준금리 및 시장금리 정보를 조회합니다.

    Args:
        rate_type (str): 금리 유형 (한국은행 기준금리, 미국 연방기금금리, 코픽스 중 하나).
    Returns:
        InterestRateData: 현재 금리, 이전 금리, 변경일, 다음 회의 일정, 금리 전망.
    """
    for key, data in INTEREST_RATES.items():
        if rate_type in key or key in rate_type:
            return data
    return InterestRateData(
        rate_type=rate_type,
        current_rate=0.0,
        previous_rate=0.0,
        change_date="N/A",
        next_meeting_date="N/A",
        outlook=f"'{rate_type}' 금리 정보를 찾을 수 없습니다. 한국은행 기준금리, 미국 연방기금금리, 코픽스 중 선택하세요.",
    )
