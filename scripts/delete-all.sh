#!/usr/bin/env bash
# =============================================================================
#  delete-all.sh — Finance RAG Agent 전체 리소스 삭제 (역순)
#    Top Agent → Sub-Agents → Flow → Tools → Knowledge Base → Connection
# =============================================================================
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[OK]${NC}    $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }

source venv/bin/activate

echo ""
warn "이 스크립트는 모든 Finance RAG Agent 리소스를 삭제합니다."
read -r -p "계속하시겠습니까? (yes/no): " confirm
[[ "$confirm" != "yes" ]] && echo "취소됨." && exit 0
echo ""

# Top Agent
orchestrate agents remove -n finance_rag_agent --kind native 2>&1 || warn "finance_rag_agent 없음(skip)"
ok "finance_rag_agent 삭제"

# Sub-Agents
orchestrate agents remove -n exchange_rate_agent   --kind native 2>&1 || warn "exchange_rate_agent 없음(skip)"
orchestrate agents remove -n deposit_advisor_agent --kind native 2>&1 || warn "deposit_advisor_agent 없음(skip)"
orchestrate agents remove -n product_agent         --kind native 2>&1 || warn "product_agent 없음(skip)"
ok "Sub-Agents 삭제"

# Flow
orchestrate tools remove -n deposit_advisor_flow 2>&1 || warn "deposit_advisor_flow 없음(skip)"
ok "deposit_advisor_flow 삭제"

# Tools
orchestrate tools remove -n get_realtime_exchange_rates 2>&1 || warn "get_realtime_exchange_rates 없음(skip)"
orchestrate tools remove -n get_single_exchange_rate    2>&1 || warn "get_single_exchange_rate 없음(skip)"
ok "Tools 삭제"

# Knowledge Base
orchestrate knowledge-bases remove -n product_guide 2>&1 || warn "product_guide 없음(skip)"
ok "Knowledge Base 삭제"

echo ""
ok "모든 리소스 삭제 완료."
