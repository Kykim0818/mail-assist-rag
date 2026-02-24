# Mail Assistant RAG

회사 메일을 붙여넣으면 LLM이 자동으로 분류·요약하고, 저장된 메일을 기반으로 RAG Q&A 채팅을 할 수 있는 로컬 웹 애플리케이션입니다.


## Quick Start (OpenCode / LLM 원클릭 세팅)

아래 프롬프트를 OpenCode(또는 다른 AI 코딩 에이전트)에 붙여넣으면 Python/Node.js 설치부터 환경 세팅, 서버 실행까지 자동으로 완료됩니다.

### 1단계: 저장소 클론

```bash
git clone https://github.com/Kykim0818/mail-assist-rag.git
```

### 2단계: OpenCode에서 프로젝트 열기

```bash
cd mail-assist-rag
opencode
```

### 3단계: 아래 프롬프트를 그대로 붙여넣기

> `YOUR_GITHUB_TOKEN` 부분만 본인의 [GitHub Personal Access Token](https://github.com/settings/tokens)으로 교체하세요.

```
이 프로젝트(mail-assist-rag)의 로컬 개발 환경을 세팅해줘. 아래 순서대로 진행해:

0. 사전 요구사항 확인 및 설치:
   - Python 3.11+ 가 설치되어 있는지 확인 (python --version 또는 python3 --version)
   - Node.js 18+ 가 설치되어 있는지 확인 (node --version)
   - 둘 중 하나라도 없거나 버전이 낮으면 자동으로 설치해줘:
     - Windows: winget install Python.Python.3.13 && winget install OpenJS.NodeJS.LTS
     - macOS: brew install python@3.13 node
     - Linux(Ubuntu/Debian): sudo apt update && sudo apt install -y python3 python3-venv nodejs npm
   - 설치 후 python, node 명령이 동작하는지 다시 확인해줘.

1. 프로젝트 루트에 .env 파일 생성:
   GITHUB_TOKEN=YOUR_GITHUB_TOKEN
   MODEL_NAME=openai/gpt-5-mini
   EMBEDDING_MODEL=openai/text-embedding-3-small
   DB_PATH=mail_assistant.db
   CHROMA_PATH=chroma_data

2. 백엔드 세팅 (backend/ 디렉토리):
   - python -m venv .venv 으로 가상환경 생성
   - 가상환경 활성화 후 pip install -r requirements.txt && pip install pydantic-settings

3. 프론트엔드 세팅 (frontend/ 디렉토리):
   - npm install

4. 세팅 완료 후 백엔드와 프론트엔드 서버를 각각 백그라운드로 실행:
   - 백엔드: 프로젝트 루트에서 uvicorn backend.main:app --port 8000
   - 프론트엔드: frontend/ 디렉토리에서 npx vite --port 5173

5. 서버가 뜨면 http://localhost:8000/api/categories 와 http://localhost:5173 에 접속해서 정상 동작 확인해줘.

SSL 인증서 오류가 나면 .env에 SSL_VERIFY=false 를 추가해줘.
```

> **완료되면**: 브라우저에서 `http://localhost:5173` 접속 → 메일 입력 → 분석하기로 바로 사용 가능합니다.

---

## 주요 기능

- **자동 분류** — 메일 본문을 분석하여 카테고리(일정, HR/인사, 프로젝트, 공지사항 등) 자동 분류
- **자동 요약** — 핵심 정보(날짜, 장소, 담당자 등)를 추출하여 간결한 요약문 생성
- **RAG 기반 Q&A** — 저장된 메일을 벡터 검색하여 자연어 질문에 정확한 답변 + 출처 제공
- **카테고리 관리** — 카테고리 추가/수정/삭제, 메일별 카테고리 수동 변경

## 기술 스택

| 구분 | 기술 |
|---|---|
| Backend | FastAPI, Python 3.13, aiosqlite, ChromaDB, httpx |
| Frontend | React 19, TypeScript, Vite 7, Tailwind CSS 4, Axios |
| LLM | GitHub Models API (`openai/gpt-5-mini`) |
| Embedding | GitHub Models API (`openai/text-embedding-3-small`) |
| DB | SQLite (메일 데이터), ChromaDB (벡터 임베딩) |

## 사전 요구사항

- **Python 3.11+** — 없으면: Windows `winget install Python.Python.3.13` / macOS `brew install python@3.13` / Linux `sudo apt install python3`
- **Node.js 18+** — 없으면: Windows `winget install OpenJS.NodeJS.LTS` / macOS `brew install node` / Linux `sudo apt install nodejs npm`
- **GitHub Personal Access Token** — [발급 방법](https://github.com/settings/tokens)
  - GitHub Copilot Business 또는 Enterprise 구독 필요 (Models API 접근용)

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/Kykim0818/mail-assist-rag.git
cd mail-assist-rag
```

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성합니다.

```bash
# .env
GITHUB_TOKEN=ghp_여기에_실제_토큰을_입력하세요
MODEL_NAME=openai/gpt-5-mini
EMBEDDING_MODEL=openai/text-embedding-3-small
DB_PATH=mail_assistant.db
CHROMA_PATH=chroma_data
```

> **참고**: 회사 네트워크 등에서 SSL 인증서 오류가 발생하면 `.env`에 `SSL_VERIFY=false`를 추가하세요.

### 3. 백엔드 설치

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
pip install pydantic-settings
```

> **참고**: `chromadb` 설치 시 C++ 빌드가 포함되어 수 분이 소요될 수 있습니다.

### 4. 프론트엔드 설치

```bash
cd frontend
npm install
```

## 실행

터미널 2개를 열어서 각각 실행합니다.

### 백엔드 서버

```bash
# 프로젝트 루트(mail-assist-rag/)에서 실행
backend\.venv\Scripts\python.exe -m uvicorn backend.main:app --port 8000

# 또는 venv 활성화 후
uvicorn backend.main:app --port 8000
```

### 프론트엔드 서버

```bash
cd frontend
npm run dev
```

### 접속

- **웹 UI**: http://localhost:5173
- **API 문서 (Swagger)**: http://localhost:8000/docs

## 사용법

### 메일 입력

1. 사이드바에서 **메일 입력** 클릭
2. 보낸 사람, 제목(선택), 메일 본문(필수) 입력
3. **분석하기** 클릭
4. LLM이 자동으로 카테고리 분류 + 요약 생성 후 저장

### 메일 목록

1. 사이드바에서 **메일 목록** 클릭
2. 카테고리별 필터링 가능
3. 개별 메일의 요약, 분류 결과 확인

### Q&A 채팅

1. 사이드바에서 **Q&A 채팅** 클릭
2. 저장된 메일에 대해 자연어로 질문
3. RAG 기반으로 관련 메일을 검색하여 답변 + 출처 표시

**예시 질문:**
- "다음 회의 일정이 언제야?"
- "연차 관련 안내 내용 알려줘"
- "AI 챗봇 프로젝트 릴리즈 일정은?"

## 프로젝트 구조

```
mail-assist-rag/
├── backend/
│   ├── db/
│   │   ├── sqlite.py          # SQLite 스키마 및 CRUD
│   │   └── chromadb.py        # ChromaDB 벡터 저장소
│   ├── services/
│   │   ├── llm.py             # GitHub Models API 클라이언트
│   │   ├── classifier.py      # 메일 분류 + 요약
│   │   ├── embeddings.py      # 임베딩 생성 및 저장
│   │   └── rag.py             # RAG 검색 + 답변 생성
│   ├── routers/
│   │   ├── emails.py          # 메일 API (POST/GET/PUT/DELETE)
│   │   ├── categories.py      # 카테고리 API (CRUD)
│   │   └── chat.py            # Q&A 채팅 API
│   ├── prompts/
│   │   ├── classify.txt       # 분류/요약 프롬프트
│   │   └── qa.txt             # RAG Q&A 프롬프트
│   ├── main.py                # FastAPI 앱 진입점
│   ├── config.py              # 환경 설정
│   ├── models.py              # Pydantic 스키마
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/
│       │   ├── EmailInput.tsx  # 메일 입력 페이지
│       │   ├── EmailList.tsx   # 메일 목록 페이지
│       │   └── Chat.tsx        # Q&A 채팅 페이지
│       ├── components/
│       │   ├── Layout.tsx      # 레이아웃 컴포넌트
│       │   └── Sidebar.tsx     # 사이드바 네비게이션
│       ├── api/
│       │   └── client.ts       # Axios API 클라이언트
│       ├── App.tsx
│       └── main.tsx
├── .env                        # 환경 변수 (git에 포함되지 않음)
├── .gitignore
└── pyproject.toml
```

## API 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| `POST` | `/api/emails` | 메일 입력 → 분류/요약/저장 |
| `GET` | `/api/emails` | 메일 목록 조회 (카테고리 필터) |
| `GET` | `/api/emails/{id}` | 메일 상세 조회 |
| `PUT` | `/api/emails/{id}/category` | 메일 카테고리 수동 변경 |
| `DELETE` | `/api/emails/{id}` | 메일 삭제 |
| `GET` | `/api/categories` | 카테고리 목록 |
| `POST` | `/api/categories` | 카테고리 추가 |
| `PUT` | `/api/categories/{id}` | 카테고리 수정 |
| `DELETE` | `/api/categories/{id}` | 카테고리 삭제 |
| `POST` | `/api/chat` | RAG Q&A 채팅 |

## 테스트

```bash
# 프로젝트 루트에서 실행 (venv 활성화 상태)
pytest                          # 전체 테스트 (41개)
pytest -m "not integration"     # 유닛 테스트만 (32개)
pytest -m integration           # 통합 테스트만 (9개)
```

## 환경 변수 참조

| 변수 | 기본값 | 설명 |
|---|---|---|
| `GITHUB_TOKEN` | — | GitHub Personal Access Token (필수) |
| `MODEL_NAME` | `openai/gpt-5-mini` | 채팅 모델명 |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | 임베딩 모델명 |
| `DB_PATH` | `mail_assistant.db` | SQLite DB 파일 경로 |
| `CHROMA_PATH` | `chroma_data` | ChromaDB 저장 디렉토리 |
| `SSL_VERIFY` | `true` | SSL 인증서 검증 (`false`로 설정 시 비활성화) |

## 라이선스

MIT
