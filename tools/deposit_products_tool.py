"""
적금 상품 정보 조회 도구 (Deposit Products Info Tool)

PDF 파일에서 적금 상품 A/B/C 정보를 읽어 반환합니다.
docext(Document Processing) 대신 pypdf로 직접 추출하여 SaaS 환경에서도 동작합니다.
"""

import os
from ibm_watsonx_orchestrate.agent_builder.tools import tool, ToolPermission
from pydantic import BaseModel, Field


class DepositProductsInfo(BaseModel):
    product_a: str = Field(description="상품 A (안심 정기적금) 상세 정보")
    product_b: str = Field(description="상품 B (청년 희망 적금) 상세 정보")
    product_c: str = Field(description="상품 C (시니어 프리미엄 적금) 상세 정보")
    summary: str   = Field(description="3개 상품 비교 요약")


@tool(permission=ToolPermission.READ_ONLY)
def get_deposit_products_info() -> DepositProductsInfo:
    """적금 상품 안내 PDF에서 상품 A, B, C의 상세 정보를 읽어 반환합니다.

    Returns:
        DepositProductsInfo: 상품 A(안심 정기적금), B(청년 희망 적금), C(시니어 프리미엄 적금) 상세 정보와 비교 요약.
    """
    # PDF 경로 — 이 파일과 동일 패키지 기준 상대 경로로 탐색
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(base_dir, "knowledge-bases", "deposit_products.pdf")

    if os.path.exists(pdf_path):
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            full_text = "\n".join(
                (page.extract_text() or "") for page in reader.pages
            )
        except Exception:
            full_text = ""
    else:
        full_text = ""

    # PDF 추출 실패 시 하드코딩 fallback
    if not full_text.strip():
        product_a = (
            "상품 A — 안심 정기적금\n"
            "대상: 만 18세 이상 전체\n"
            "금리: 연 3.8% (확정금리)\n"
            "납입 방식: 매월 정기납입\n"
            "월 납입 한도: 10만~50만 원\n"
            "가입 기간: 12개월 / 24개월\n"
            "특별 혜택: 없음 (기본형)\n"
            "예금자 보호: 예금보험공사 5,000만 원 한도\n"
            "추천 목적: 처음 적금을 시작하는 사회 초년생, 단기 목돈 마련"
        )
        product_b = (
            "상품 B — 청년 희망 적금\n"
            "대상: 만 19~34세 청년 (병역 이행기간 최대 6년 추가 인정)\n"
            "소득 조건: 총급여 7,500만 원 이하\n"
            "금리: 연 5.0% (기본 4.5% + 청년 우대 0.5%)\n"
            "납입 방식: 자유납입\n"
            "월 납입 한도: 최대 70만 원\n"
            "가입 기간: 24개월 고정\n"
            "특별 혜택: 비과세 혜택(600만 원 한도), 저축 장려금 2~4%\n"
            "추천 목적: 청년 재테크, 전세자금·결혼자금 마련"
        )
        product_c = (
            "상품 C — 시니어 프리미엄 적금\n"
            "대상: 만 55세 이상\n"
            "금리: 연 5.0% (기본 4.0% + 시니어 우대 0.8% + 장기 우대 0.2%)\n"
            "납입 방식: 매월 정기납입\n"
            "월 납입 한도: 20만~100만 원\n"
            "가입 기간: 24개월 / 36개월\n"
            "특별 혜택: 건강검진 바우처(연 1회), 금융 상담 우선 배정\n"
            "만 65세 이상: 비과세 종합저축 한도(5,000만 원) 활용 시 이자소득세 면제\n"
            "추천 목적: 은퇴 후 노후 준비, 의료비 준비"
        )
        summary = (
            "상품 비교 요약\n"
            "- 상품 A(안심 정기적금): 만 18세 이상 전체 / 연 3.8% / 12·24개월 / 기본형\n"
            "- 상품 B(청년 희망 적금): 만 19~34세 / 연 5.0% / 24개월 / 비과세+장려금\n"
            "- 상품 C(시니어 프리미엄): 만 55세 이상 / 연 5.0% / 24·36개월 / 건강검진 바우처"
        )
        return DepositProductsInfo(
            product_a=product_a,
            product_b=product_b,
            product_c=product_c,
            summary=summary,
        )

    # PDF 텍스트를 상품별로 분리
    def _extract_section(text: str, start_marker: str, end_marker: str) -> str:
        s = text.find(start_marker)
        e = text.find(end_marker, s + 1) if end_marker else len(text)
        if s == -1:
            return text[:800]
        return text[s: e if e != -1 else len(text)].strip()[:1200]

    product_a = _extract_section(full_text, "상품 A", "상품 B")
    product_b = _extract_section(full_text, "상품 B", "상품 C")
    product_c = _extract_section(full_text, "상품 C", "상품 종합 비교")
    summary   = _extract_section(full_text, "상품 종합 비교", "")

    return DepositProductsInfo(
        product_a=product_a or "상품 A 정보를 추출하지 못했습니다.",
        product_b=product_b or "상품 B 정보를 추출하지 못했습니다.",
        product_c=product_c or "상품 C 정보를 추출하지 못했습니다.",
        summary=summary   or "비교 요약을 추출하지 못했습니다.",
    )
