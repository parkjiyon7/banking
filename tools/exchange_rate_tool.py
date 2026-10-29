"""
실시간 환율 조회 도구 (Exchange Rate Tool)
한국수출입은행 환율 API를 사용하여 실시간 환율 정보를 조회합니다.

API: https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON
     ?authkey=<KEY>&searchdate=<YYYYMMDD>&data=AP01

config/api_config.yaml 에서 URL과 authkey를 관리합니다.
"""

import os
import yaml
import requests
from datetime import datetime, timedelta, timezone
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from pydantic import BaseModel, Field


# ── 상수 ───────────────────────────────────────────────────────────────────────

KST = timezone(timedelta(hours=9))


# ── 내부 유틸 ─────────────────────────────────────────────────────────────────

# wxO 서버에 config 파일이 없을 경우를 위한 기본값 (로컬 파일이 있으면 덮어씀)
_DEFAULT_CONFIG = {
    "base_url":  "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON",
    "authkey":   "fQPJiBworRRDQ0jHnVJRIxMadqVOqnDq",
    "data_code": "AP01",
    "timeout_seconds": 10,
}


def _load_config() -> dict:
    """config/api_config.yaml 이 있으면 로드하고, 없으면 _DEFAULT_CONFIG 를 사용합니다."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config", "api_config.yaml",
    )
    if os.path.exists(config_path):
        try:
            with open(config_path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            loaded = data.get("exchange_rate_api", {})
            if loaded:
                return loaded
        except Exception:
            pass
    return _DEFAULT_CONFIG


def _latest_business_date() -> str:
    """KST 기준 가장 최근 영업일을 YYYYMMDD 로 반환합니다 (주말이면 직전 금요일)."""
    d = datetime.now(KST)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def _prev_business_date(yyyymmdd: str) -> str:
    """주어진 날짜의 직전 영업일(월~금)을 반환합니다."""
    d = datetime.strptime(yyyymmdd, "%Y%m%d") - timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def _resolve_date(searchdate: str) -> str:
    """
    searchdate 를 실제 조회용 YYYYMMDD 날짜 문자열로 변환합니다.
    - 'today' 또는 비어있거나 인식 불가한 값 → KST 기준 최근 영업일 자동 계산
    - 'YYYYMMDD' 형식 → 그대로 사용
    """
    cleaned = searchdate.strip().lower()
    if cleaned in ("today", "오늘", "", "null", "none"):
        return _latest_business_date()
    # YYYYMMDD 형식 검증
    try:
        datetime.strptime(cleaned, "%Y%m%d")
        return cleaned
    except ValueError:
        return _latest_business_date()


def _call_api(searchdate: str) -> list:
    """환율 API 호출. 실패 또는 빈 응답이면 [] 반환."""
    cfg = _load_config()
    base_url  = cfg.get("base_url", "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON")
    authkey   = cfg.get("authkey", "")
    data_code = cfg.get("data_code", "AP01")
    timeout   = cfg.get("timeout_seconds", 10)
    try:
        resp = requests.get(
            base_url,
            params={"authkey": authkey, "searchdate": searchdate, "data": data_code},
            timeout=timeout,
        )
        resp.raise_for_status()
        result = resp.json()
        return result if isinstance(result, list) else []
    except Exception:
        return []


def _fetch(searchdate: str) -> tuple:
    """
    날짜를 확정한 뒤 API를 호출합니다.
    당일 데이터는 한국수출입은행 기준 평일 오전 11시 이후 제공됩니다.
    데이터가 없으면 직전 영업일로 최대 10회 재시도합니다.
    반환: (데이터 리스트, 실제 조회된 날짜 YYYYMMDD)
    """
    date = _resolve_date(searchdate)
    for _ in range(10):
        raw = _call_api(date)
        if raw:
            return raw, date
        date = _prev_business_date(date)
    return [], date


# ── 응답 스키마 ───────────────────────────────────────────────────────────────

class ExchangeRateListResult(BaseModel):
    search_date: str  = Field(description="조회 기준일 (YYYYMMDD)")
    total_count: int  = Field(description="조회된 통화 수")
    rates: list       = Field(description="통화별 환율 목록")
    source: str       = Field(description="데이터 출처")


class SingleExchangeRateResult(BaseModel):
    search_date: str  = Field(description="조회 기준일 (YYYYMMDD)")
    cur_unit: str     = Field(description="통화 코드 (예: USD)")
    cur_nm: str       = Field(description="통화명 (예: 미국 달러)")
    deal_bas_r: str   = Field(description="매매 기준율 (원화 기준, 예: 1 달러 = 1,324.60원)")
    ttb: str          = Field(description="전신환 매입률 (은행 매입가)")
    tts: str          = Field(description="전신환 매도율 (은행 매도가)")
    source: str       = Field(description="데이터 출처")


# ── 도구 정의 ─────────────────────────────────────────────────────────────────

@tool(permission=ToolPermission.READ_ONLY)
def get_all_exchange_rates(searchdate: str) -> ExchangeRateListResult:
    """한국수출입은행 기준 전체 통화의 환율을 조회합니다. 기준통화는 원화(KRW)입니다.

    Args:
        searchdate (str): 조회 기준일. 사용자가 날짜를 지정하지 않은 경우 반드시 'today'를 입력하세요.
            'today' 입력 시 KST(한국 표준시) 기준 가장 최근 영업일로 자동 설정됩니다.
            특정 날짜를 조회할 경우 YYYYMMDD 형식으로 입력하세요 (예: 20261020).
            주말 및 공휴일에는 직전 영업일 데이터가 자동 반환됩니다.
    Returns:
        ExchangeRateListResult: 전체 통화별 매매 기준율, 전신환 매입률, 전신환 매도율 목록.
    """
    raw, date = _fetch(searchdate)

    rates = [
        {
            "통화코드":     item.get("cur_unit", ""),
            "통화명":       item.get("cur_nm", ""),
            "매매기준율":   item.get("deal_bas_r", ""),
            "전신환매입률": item.get("ttb", ""),
            "전신환매도율": item.get("tts", ""),
        }
        for item in raw
        if item.get("result") == 1
    ]

    return ExchangeRateListResult(
        search_date=date,
        total_count=len(rates),
        rates=rates,
        source="한국수출입은행 환율 API (https://oapi.koreaexim.go.kr)",
    )


@tool(permission=ToolPermission.READ_ONLY)
def get_single_exchange_rate(currency: str, searchdate: str) -> SingleExchangeRateResult:
    """특정 통화 한 가지의 원화(KRW) 기준 환율을 조회합니다.

    Args:
        currency (str): 조회할 통화 코드 (예: USD, EUR, JPY, GBP, CNY, AUD, HKD).
        searchdate (str): 조회 기준일. 사용자가 날짜를 지정하지 않은 경우 반드시 'today'를 입력하세요.
            'today' 입력 시 KST(한국 표준시) 기준 가장 최근 영업일로 자동 설정됩니다.
            특정 날짜를 조회할 경우 YYYYMMDD 형식으로 입력하세요 (예: 20261020).
            주말 및 공휴일에는 직전 영업일 데이터가 자동 반환됩니다.
    Returns:
        SingleExchangeRateResult: 해당 통화의 KRW 기준 매매 기준율, 전신환 매입률, 전신환 매도율.
    """
    raw, date = _fetch(searchdate)

    target = currency.upper().strip()
    for item in raw:
        if item.get("result") != 1:
            continue
        # JPY(100) 처럼 괄호가 붙는 통화 코드도 매칭
        if target in item.get("cur_unit", "").upper():
            return SingleExchangeRateResult(
                search_date=date,
                cur_unit=item.get("cur_unit", target),
                cur_nm=item.get("cur_nm", ""),
                deal_bas_r=item.get("deal_bas_r", ""),
                ttb=item.get("ttb", ""),
                tts=item.get("tts", ""),
                source="한국수출입은행 환율 API (https://oapi.koreaexim.go.kr)",
            )

    return SingleExchangeRateResult(
        search_date=date,
        cur_unit=target,
        cur_nm="해당 통화를 찾을 수 없습니다.",
        deal_bas_r="N/A",
        ttb="N/A",
        tts="N/A",
        source="한국수출입은행 환율 API (https://oapi.koreaexim.go.kr)",
    )
