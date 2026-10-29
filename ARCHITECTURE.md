# Finance RAG Agent — Architecture

금융 산업을 위한 **watsonx Orchestrate No-Code 기반 멀티 에이전트 시스템**입니다.  
Top Agent가 사용자 질문을 분류하여 3개의 전문 Sub-Agent로 라우팅합니다.

---

## 1. 전체 시스템 아키텍처

```mermaid
graph TD
    USER["👤 사용자\n(wxO Chat UI)"]

    TOP["🏛️ finance_rag_agent\n금융 AI 어시스턴트\n─────────────────\nOrchestrator\nstyle: react_core\ncollaborators: 3개\n─────────────────\n질문 분류 후\nSub-Agent로 라우팅"]

    A1["📋 product_agent\n금융 상품 안내 에이전트\n─────────────────\nRAG Q&A\nKnowledge: product_guide\n─────────────────\n문서 기반 답변\n금리·조건·혜택 안내"]

    A2["💡 deposit_advisor_agent\n적금 추천 에이전트\n─────────────────\nNo-Code Workflow\nFlow: deposit_advisor_flow\n─────────────────\nPDF 추출 + 폼 수집\n맞춤 적금 추천"]

    A3["💱 exchange_rate_agent\n실시간 환율 조회 에이전트\n─────────────────\nOpenAPI 연동\nAPI: 한국수출입은행\n─────────────────\n실시간 환율 조회\n전신환 매입·매도율 제공"]

    DOC["📄 financial_products_guide.txt\n예금·적금·대출·투자·외환\n상품 정보 문서"]
    PDF["📑 deposit_products.pdf\n상품 A 안심 정기적금\n상품 B 청년 희망 적금\n상품 C 시니어 프리미엄 적금"]
    API["🌐 한국수출입은행 환율 API\nhttps://oapi.koreaexim.go.kr\n/site/program/financial/exchangeJSON"]
    CFG["⚙️ config/api_config.yaml\nAPI URL·authkey 관리"]

    USER -->|"금융 질문 입력"| TOP
    TOP -->|"상품 금리·조건 질문"| A1
    TOP -->|"적금 추천 요청"| A2
    TOP -->|"환율 조회 요청"| A3

    A1 --- DOC
    A2 --- PDF
    A3 --- CFG
    A3 -->|"HTTP GET"| API

    A1 -->|"답변 반환"| TOP
    A2 -->|"추천 결과 반환"| TOP
    A3 -->|"실시간 환율 반환"| TOP
    TOP -->|"최종 답변"| USER

    style TOP fill:#e3f2fd,stroke:#1565c0,color:#000
    style A1  fill:#e8f5e9,stroke:#2e7d32,color:#000
    style A2  fill:#fff3e0,stroke:#e65100,color:#000
    style A3  fill:#f3e5f5,stroke:#6a1b9a,color:#000
    style DOC fill:#fafafa,stroke:#9e9e9e,color:#000
    style PDF fill:#fafafa,stroke:#9e9e9e,color:#000
    style API fill:#e8eaf6,stroke:#3949ab,color:#000
    style CFG fill:#fafafa,stroke:#9e9e9e,color:#000
```

---

## 2. wxO No-Code 빌더 UI — 전체 에이전트 연결 뷰

> wxO Agent Builder 화면에서 바라본 에이전트 연결 구조입니다.
> 각 박스는 wxO UI의 **에이전트 카드** 한 장에 대응합니다.

```mermaid
graph LR
    subgraph WXO["🖥️  watsonx Orchestrate — Agent Builder 캔버스"]
        direction LR

        subgraph TOP_BOX["Top Agent (Orchestrator)"]
            TOP_CARD["🏛️ finance_rag_agent\n━━━━━━━━━━━━━━━━━━\n■ Name: finance_rag_agent\n■ Display: 금융 AI 어시스턴트\n■ Style: react_core\n■ LLM: groq/openai/gpt-oss-120b\n■ Collaborators ↓"]
        end

        subgraph SUB1_BOX["Sub-Agent 1"]
            S1["📚 product_agent\n━━━━━━━━━━━━━━━━━━\n■ Display: 금융 상품 안내 에이전트\n■ Style: react_core\n■ LLM: groq/openai/gpt-oss-120b\n■ Knowledge Base: product_guide\n■ RAG 기반 문서 검색 답변"]
        end

        subgraph SUB2_BOX["Sub-Agent 2"]
            S2["📋 deposit_advisor_agent\n━━━━━━━━━━━━━━━━━━\n■ Display: 적금 추천 에이전트\n■ Style: react_core\n■ LLM: groq/openai/gpt-oss-120b\n■ Tool: deposit_advisor_flow\n■ suppress_summarization: true"]
        end

        subgraph SUB3_BOX["Sub-Agent 3"]
            S3["💱 exchange_rate_agent\n━━━━━━━━━━━━━━━━━━\n■ Display: 실시간 환율 조회 에이전트\n■ Style: react_core\n■ LLM: groq/openai/gpt-oss-120b\n■ Tools: get_single / get_all\n■ 한국수출입은행 API 연동"]
        end

        TOP_CARD -->|"collaborator"| S1
        TOP_CARD -->|"collaborator"| S2
        TOP_CARD -->|"collaborator"| S3
    end

    style WXO fill:#f0f4ff,stroke:#3b5bdb,color:#000
    style TOP_BOX fill:#e3f2fd,stroke:#1565c0,color:#000
    style SUB1_BOX fill:#e8f5e9,stroke:#2e7d32,color:#000
    style SUB2_BOX fill:#fff3e0,stroke:#e65100,color:#000
    style SUB3_BOX fill:#f3e5f5,stroke:#6a1b9a,color:#000
```

---

## 3. wxO No-Code 빌더 UI — deposit_advisor_flow 워크플로우 캔버스

> wxO Workflow Builder 화면에서 바라본 `deposit_advisor_flow`의 노드 배치입니다.
> 각 박스는 워크플로우 캔버스의 **노드 카드** 하나에 대응합니다.

```mermaid
flowchart LR
    subgraph CANVAS["🖥️  watsonx Orchestrate — Workflow Builder 캔버스\n        deposit_advisor_flow  ·  적금 상품 추천 워크플로우"]
        direction LR

        N_START(["▶ START"])

        subgraph N1_BOX["Node 1 — Document Extraction"]
            N1["📄 docext\n━━━━━━━━━━━━━━━━━━━━━━━━━\n■ Name: extract_deposit_info\n■ Display: 적금 상품 정보 추출\n■ LLM: mistral-small-3-1-24b\n■ Method: classic\n■ Fields:\n    · full_text (string)\n      PDF 전체 텍스트 추출\n━━━━━━━━━━━━━━━━━━━━━━━━━\n📥 Input: deposit_products.pdf\n📤 Output: extracted_fields"]
        end

        subgraph N2_BOX["Node 2 — User Form"]
            N2["📋 userflow\n━━━━━━━━━━━━━━━━━━━━━━━━━\n■ Name: collect_customer_info\n■ Display: 고객 정보 입력\n  Form: customer_info_form\n  ┌────────────────────────┐\n  │ 나이 (만 나이)         │  ← number\n  │ 저축 목적              │  ← text\n  │ 선호 가입 기간         │  ← text\n  │ 월 납입 가능 금액(만원)│  ← number\n  └────────────────────────┘\n━━━━━━━━━━━━━━━━━━━━━━━━━\n📥 Input: 사용자 폼 입력\n📤 Output: customer_info"]
        end

        subgraph N3_BOX["Node 3 — LLM Prompt"]
            N3["🤖 prompt\n━━━━━━━━━━━━━━━━━━━━━━━━━\n■ Name: recommend_product\n■ Display: 맞춤 적금 상품 추천\n■ LLM: groq/openai/gpt-oss-120b\n■ System Prompt: 금융 상담사\n  · 연령 조건 필터\n  · 선호 기간 매칭\n  · 만기 수령액 최고 추천\n■ User Prompt 변수 바인딩:\n  · {product_data}  ← docext.output\n  · {customer_info} ← userflow.output\n━━━━━━━━━━━━━━━━━━━━━━━━━\n📤 Output: 추천 상품 + 수령액 + 유의사항"]
        end

        N_END(["⏹ END"])

        N_START --> N1_BOX
        N1_BOX  --> N2_BOX
        N2_BOX  --> N3_BOX
        N3_BOX  --> N_END
    end

    style CANVAS  fill:#fffde7,stroke:#f9a825,color:#000
    style N1_BOX  fill:#e8eaf6,stroke:#3949ab,color:#000
    style N2_BOX  fill:#e0f2f1,stroke:#00695c,color:#000
    style N3_BOX  fill:#e8f5e9,stroke:#2e7d32,color:#000
```

---

## 4. wxO No-Code 빌더 UI — Tool Import 뷰

> wxO **Skills & Tools** 탭에서 바라본 임포트된 도구 목록입니다.

```mermaid
graph TD
    subgraph TOOLS_TAB["🖥️  watsonx Orchestrate — Skills & Tools 탭"]
        direction TB

        subgraph PY_TOOL["Python Tool — exchange_rate_tool.py"]
            T1["🔧 get_all_exchange_rates\n━━━━━━━━━━━━━━━━━━━━━━━━━\n■ Permission: READ_ONLY\n■ Args:\n    · searchdate: str\n      ('today' or YYYYMMDD)\n■ Returns: ExchangeRateListResult\n    · search_date, total_count\n    · rates[ ]: 40+ 통화 목록\n    · source: 한국수출입은행"]

            T2["🔧 get_single_exchange_rate\n━━━━━━━━━━━━━━━━━━━━━━━━━\n■ Permission: READ_ONLY\n■ Args:\n    · currency: str (예: USD)\n    · searchdate: str\n■ Returns: SingleExchangeRateResult\n    · cur_unit, cur_nm\n    · deal_bas_r (매매기준율)\n    · ttb (전신환 매입률)\n    · tts (전신환 매도율)\n    · source: 한국수출입은행"]
        end

        subgraph FLOW_TOOL["Flow Tool — deposit_advisor_flow.py"]
            T3["🔄 deposit_advisor_flow\n━━━━━━━━━━━━━━━━━━━━━━━━━\n■ Kind: @flow\n■ Input: DocumentProcessingCommonInput\n  (PDF 파일 업로드)\n■ Nodes: docext → userflow → prompt\n■ suppress_agent_summarization: True\n■ Output: 맞춤 적금 추천 텍스트"]
        end

        subgraph KB_TOOL["Knowledge Base — product_guide.yaml"]
            T4["📚 product_guide\n━━━━━━━━━━━━━━━━━━━━━━━━━\n■ Kind: knowledge_base\n■ Embedding: ibm/slate-125m-english-rtrvr-v2\n■ Source: financial_products_guide.txt\n  (예금·적금·대출·투자·외환 상품 정보)\n■ Retrieval: 벡터 검색 (RAG)"]
        end
    end

    style TOOLS_TAB  fill:#f8f9ff,stroke:#3b5bdb,color:#000
    style PY_TOOL    fill:#e8f5e9,stroke:#2e7d32,color:#000
    style FLOW_TOOL  fill:#fff3e0,stroke:#e65100,color:#000
    style KB_TOOL    fill:#e3f2fd,stroke:#1565c0,color:#000
```

---

## 5. 전체 워크플로우 다이어그램 (사용자 시점)

```mermaid
flowchart TD
    START(["👤 사용자 질문"])

    TOP_LLM{"🏛️ finance_rag_agent\n질문 카테고리 판단"}

    subgraph AGENT1["Sub-Agent 1 — product_agent (금융 상품 안내)"]
        direction TB
        A1_IN["질문 수신\n예: '청년 우대 적금 조건이 뭐야?'"]
        A1_RAG["문서 검색\nproduct_guide\n(financial_products_guide.txt)"]
        A1_LLM["LLM 답변 생성\n금리·조건·혜택·유의사항 포함"]
        A1_IN --> A1_RAG --> A1_LLM
    end

    subgraph AGENT2["Sub-Agent 2 — deposit_advisor_agent (적금 추천)"]
        direction TB
        A2_IN["적금 추천 요청 수신\n예: '나한테 맞는 적금 추천해줘'"]
        A2_FLOW["deposit_advisor_flow 실행"]

        subgraph FLOW["@flow 내부 — No-Code Workflow"]
            direction LR
            F1["① docext\ndeposit_products.pdf 업로드\n상품명·금리·대상연령·혜택 추출"]
            F2["② userflow 폼\n나이 입력\n저축 목적 선택\n선호 기간 선택\n월 납입 예산 입력"]
            F3["③ prompt (LLM)\n상품 정보 + 고객 정보\n→ 상품 A/B/C 중 최적 추천\n예상 수령액 + 유의사항"]
            F1 --> F2 --> F3
        end

        A2_IN --> A2_FLOW --> FLOW
    end

    subgraph AGENT3["Sub-Agent 3 — exchange_rate_agent (실시간 환율)"]
        direction TB
        A3_IN["환율 조회 요청 수신\n예: '달러 환율이 얼마야?'"]
        A3_CFG["_DEFAULT_CONFIG 로드\nURL·authkey 확인"]
        A3_API["한국수출입은행 환율 API 호출\nGET /exchangeJSON\n?authkey=...&searchdate=...&data=AP01"]
        A3_PARSE["응답 파싱\ncur_unit / cur_nm\ndeal_bas_r / ttb / tts"]
        A3_ANS["환율 표 형식 답변\n매매 기준율·매입률·매도율 포함"]
        A3_IN --> A3_CFG --> A3_API --> A3_PARSE --> A3_ANS
    end

    END_NODE(["💬 사용자에게 최종 답변 전달"])

    START --> TOP_LLM
    TOP_LLM -->|"상품 금리·조건 질문"| AGENT1
    TOP_LLM -->|"적금 추천 요청"| AGENT2
    TOP_LLM -->|"환율 조회 요청"| AGENT3

    AGENT1 --> END_NODE
    AGENT2 --> END_NODE
    AGENT3 --> END_NODE

    style FLOW   fill:#fff8e1,stroke:#f9a825
    style AGENT1 fill:#e8f5e9,stroke:#2e7d32
    style AGENT2 fill:#fff3e0,stroke:#e65100
    style AGENT3 fill:#f3e5f5,stroke:#6a1b9a
```

---

## 6. 임포트 순서 (wxO CLI)

```mermaid
flowchart LR
    K["① Knowledge Base\nproduct_guide.yaml"]
    T["② Tools\nexchange_rate_tool.py"]
    F["③ Flow\ndeposit_advisor_flow.py"]
    SA["④ Sub-Agents\nproduct_agent\ndeposit_advisor_agent\nexchange_rate_agent"]
    TA["⑤ Top Agent\nfinance_rag_agent"]

    K --> T --> F --> SA --> TA

    style K  fill:#fce4ec,stroke:#c62828
    style T  fill:#e8f5e9,stroke:#2e7d32
    style F  fill:#fff3e0,stroke:#e65100
    style SA fill:#e3f2fd,stroke:#1565c0
    style TA fill:#e0f2f1,stroke:#00695c
```

```bash
# 임포트 실행
source venv/bin/activate
orchestrate env activate wxO-apac --api-key "$IBM_CLOUD_API_KEY"
chmod +x scripts/import-all.sh && ./scripts/import-all.sh
```

---

## 7. Sub-Agent 상세 설명

### Sub-Agent 1 — `product_agent` (금융 상품 안내 에이전트)

| 항목 | 내용 |
|------|------|
| **역할** | 금융 상품 문서를 기반으로 고객의 질문에 답변하는 RAG 에이전트 |
| **방식** | Native Agent + 문서 검색 (No-Code) |
| **지식 소스** | `financial_products_guide.txt` — 예금·적금·대출·투자·외환 상품 정보 |
| **대표 질문** | "청년 우대 적금 가입 조건이 뭐야?", "주택담보대출 한도가 얼마야?" |
| **답변 방식** | 문서에서 관련 정보 검색 → 금리·조건·혜택·유의사항 구조화 답변 |

---

### Sub-Agent 2 — `deposit_advisor_agent` (적금 추천 에이전트)

| 항목 | 내용 |
|------|------|
| **역할** | PDF 문서에서 상품 정보를 추출하고, 고객 정보를 수집해 맞춤 적금 추천 |
| **방식** | Native Agent + `@flow` (No-Code Workflow) |
| **Flow 구성** | `docext` → `userflow` 폼 → `prompt` (LLM 추천) |
| **데이터 소스** | `deposit_products.pdf` — 상품 A / B / C |
| **대표 질문** | "어떤 적금이 좋을까?", "나한테 맞는 적금 추천해줘" |

**deposit_products.pdf 상품 구성:**

| 상품 | 대상 | 최대 금리 | 특징 |
|------|------|---------|------|
| 상품 A — 안심 정기적금 | 만 18세 이상 전체 | 연 3.8% | 기본형, 정기납입 |
| 상품 B — 청년 희망 적금 | 만 19~34세 | 연 5.0% | 비과세 + 저축 장려금 |
| 상품 C — 시니어 프리미엄 적금 | 만 55세 이상 | 연 5.0% | 건강검진 바우처 |

---

### Sub-Agent 3 — `exchange_rate_agent` (실시간 환율 조회 에이전트)

| 항목 | 내용 |
|------|------|
| **역할** | 한국수출입은행 환율 API를 통해 실시간 환율 정보 제공 |
| **방식** | Native Agent + OpenAPI `@tool` |
| **API** | `https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON` |
| **파라미터** | `authkey`, `searchdate` (YYYYMMDD), `data=AP01` |
| **설정 관리** | `_DEFAULT_CONFIG` 상수 내장 (서버 환경 fallback) |
| **도구** | `get_single_exchange_rate` (단일 통화), `get_all_exchange_rates` (전체 통화) |
| **대표 질문** | "달러 환율이 얼마야?", "달러·유로·엔화 환율을 한번에 알려줘" |

**API 응답 주요 필드:**

| 필드 | 설명 | 예시 |
|------|------|------|
| `cur_unit` | 통화 코드 | `USD`, `JPY(100)` |
| `cur_nm` | 통화명 (한국어) | `미국 달러` |
| `deal_bas_r` | 매매 기준율 | `1,331.50` |
| `ttb` | 전신환 매입률 (은행 매입가) | `1,317.96` |
| `tts` | 전신환 매도율 (은행 매도가) | `1,345.04` |

---

## 8. 파일 구조

```
banking/
├── ARCHITECTURE.md                      이 문서
│
├── index.html                           금융 홈화면 + wxO embedded agent
│
├── agents/
│   ├── finance_rag_agent.yaml           Top Agent (Orchestrator)
│   ├── product_agent.yaml               Sub-Agent 1 — 상품 안내
│   ├── deposit_advisor_agent.yaml       Sub-Agent 2 — 적금 추천
│   └── exchange_rate_agent.yaml         Sub-Agent 3 — 환율 조회
│
├── knowledge-bases/
│   ├── product_guide.yaml               Sub-Agent 1용 문서 검색 정의
│   ├── financial_products_guide.txt     금융 상품 안내 문서
│   └── deposit_products.pdf             적금 상품 A/B/C 안내 PDF
│
├── tools/
│   ├── deposit_advisor_flow.py          Sub-Agent 2용 @flow
│   └── exchange_rate_tool.py            Sub-Agent 3용 @tool (한국수출입은행 API)
│
├── config/
│   └── api_config.yaml                  API URL·authkey 관리 (⚠️ .gitignore 권장)
│
└── scripts/
    ├── import-all.sh                    전체 임포트 (KB→Tools→Flow→Agents)
    └── delete-all.sh                    전체 삭제 (역순)
```

---

## 9. 테스트 시나리오

| 시나리오 | 입력 예시 | 처리 경로 |
|---------|---------|---------|
| 상품 조건 질문 | "청년 우대 적금 가입 조건이 뭐야?" | Top → product_agent → 문서 검색 → 답변 |
| 대출 한도 질문 | "신용대출 한도가 얼마야?" | Top → product_agent → 문서 검색 → 답변 |
| 적금 추천 요청 | "나한테 맞는 적금 추천해줘." | Top → deposit_advisor_agent → Flow(PDF 추출+폼) → LLM 추천 |
| 환율 단일 조회 | "지금 달러 환율이 얼마야?" | Top → exchange_rate_agent → 한국수출입은행 API → 실시간 환율 |
| 환율 다중 조회 | "달러, 유로, 엔화 환율 한번에 알려줘." | Top → exchange_rate_agent → API → 표 형식 답변 |
