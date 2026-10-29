#!/usr/bin/env bash
# =============================================================================
#  import-all.sh — Finance RAG Agent 전체 리소스 임포트
#
#  의존성 순서:
#    Connection → Knowledge Base → Tools → Flow → Sub-Agents → Top Agent
#
#  실행 전 준비:
#    1. config/api_config.yaml 에 환율 API URL 및 key 입력
#    2. orchestrate env activate <env-name> --api-key "$API_KEY" 실행
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
info() { echo -e "${BLUE}[INFO]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }

source venv/bin/activate
echo ""
echo "================================================="
echo "  Finance RAG Agent — 전체 임포트 시작"
echo "================================================="
echo ""

# ── Step 1: Knowledge Base ─────────────────────────────────────────────────
echo ""
info "[1/5] Knowledge Base 임포트..."
(cd knowledge-bases && orchestrate knowledge-bases import -f product_guide.yaml)
ok "product_guide 임포트 완료 — 인덱싱은 백그라운드에서 진행됩니다."
info "  인덱싱 상태 확인: orchestrate knowledge-bases status -n product_guide"

# ── Step 2: Tools ───────────────────────────────────────────────────────────
echo ""
info "[2/5] Tools 임포트..."
orchestrate tools import -k python -f tools/exchange_rate_tool.py
ok "exchange_rate_tool (get_all_exchange_rates, get_single_exchange_rate) 임포트 완료"

# ── Step 3: Flow ────────────────────────────────────────────────────────────
echo ""
info "[3/5] Flow 임포트..."
orchestrate tools import -k flow -f tools/deposit_advisor_flow.py
ok "deposit_advisor_flow 임포트 완료"

# ── Step 4: Sub-Agents ──────────────────────────────────────────────────────
echo ""
info "[4/5] Sub-Agent 임포트 (collaborator 먼저)..."
orchestrate agents import -f agents/product_agent.yaml
ok "product_agent 임포트 완료"

orchestrate agents import -f agents/deposit_advisor_agent.yaml
ok "deposit_advisor_agent 임포트 완료"

orchestrate agents import -f agents/exchange_rate_agent.yaml
ok "exchange_rate_agent 임포트 완료"

# ── Step 5: Top Agent ───────────────────────────────────────────────────────
echo ""
info "[5/5] Top Agent 임포트..."
orchestrate agents import -f agents/finance_rag_agent.yaml
ok "finance_rag_agent (Orchestrator) 임포트 완료"

# ── 완료 안내 ───────────────────────────────────────────────────────────────
echo ""
echo "================================================="
echo "  임포트 완료!"
echo "================================================="
echo ""
ok "모든 리소스가 성공적으로 임포트되었습니다."
echo ""
echo "  다음 단계:"
echo "  1. 웹 UI에서 '금융 AI 어시스턴트' 검색 후 대화 시작"
echo ""
echo "  2. 샘플 질문:"
echo "     - 청년 우대 적금 가입 조건이 뭐야?"
echo "     - 나한테 맞는 적금 추천해줘."
echo "     - 지금 달러 환율이 얼마야?"
