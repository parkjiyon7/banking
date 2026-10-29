#!/usr/bin/env python3
"""
스마트뱅크 로컬 개발 서버
- 정적 파일 서빙 (index.html 등)
- /api/fx?searchdate=YYYYMMDD  : 한국수출입은행 환율 API 프록시 (AP01)
  · 빈 응답(비영업일·11시 이전)이면 자동으로 직전 영업일 재시도 (최대 7회)
"""
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler

AUTHKEY = "fQPJiBworRRDQ0jHnVJRIxMadqVOqnDq"
FX_URL  = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
PORT    = 8080


def prev_business_day(yyyymmdd: str) -> str:
    """주어진 날짜의 직전 영업일(월~금) 반환."""
    d = datetime.strptime(yyyymmdd, "%Y%m%d") - timedelta(days=1)
    while d.weekday() >= 5:          # 5=토, 6=일
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def fetch_fx(searchdate: str) -> tuple[list, str]:
    """
    한국수출입은행 AP01 환율 조회. 빈 응답이면 직전 영업일로 최대 7회 재시도.
    반환: (rates 리스트, 실제 조회된 날짜)
    """
    date = searchdate
    for _ in range(7):
        params = urllib.parse.urlencode({
            "authkey":    AUTHKEY,
            "searchdate": date,
            "data":       "AP01",
        })
        try:
            req = urllib.request.Request(
                f"{FX_URL}?{params}",
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
            if isinstance(result, list) and len(result) > 0:
                return result, date
        except Exception:
            pass
        date = prev_business_day(date)
    return [], date


def latest_business_date() -> str:
    """KST 기준 가장 최근 데이터가 있는 영업일 날짜 반환."""
    today = datetime.now().strftime("%Y%m%d")
    _, actual = fetch_fx(today)
    return actual


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.address_string()} {fmt % args}")

    def _json_response(self, body: bytes):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        qs     = urllib.parse.parse_qs(parsed.query)

        # ── /api/fx?searchdate=YYYYMMDD  (AP01 환율) ────────────────────
        if self.path.startswith("/api/fx"):
            searchdate = qs.get("searchdate", [""])[0] or datetime.now().strftime("%Y%m%d")
            data, actual_date = fetch_fx(searchdate)
            body = json.dumps({"date": actual_date, "rates": data}, ensure_ascii=False).encode()
            self._json_response(body)
            return

        # ── 정적 파일 ────────────────────────────────────────────────────
        super().do_GET()


if __name__ == "__main__":
    server = HTTPServer(("", PORT), Handler)
    print(f"\n  스마트뱅크 서버 시작 → http://localhost:{PORT}\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  서버 종료")
