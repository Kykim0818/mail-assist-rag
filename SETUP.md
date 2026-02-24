# Mail Assistant RAG — 자동 세팅 가이드

이 파일을 AI 코딩 에이전트(OpenCode, Cursor, Copilot 등)에 넘기면 환경 세팅부터 서버 실행까지 자동으로 완료됩니다.

> **사전 준비**: [GitHub Personal Access Token](https://github.com/settings/tokens) 발급 필요 (GitHub Copilot Business/Enterprise 구독)

---

## 세팅 프롬프트

아래 내용을 그대로 복사하여 AI 에이전트에 붙여넣으세요. `YOUR_GITHUB_TOKEN` 만 본인 토큰으로 교체하면 됩니다.

```
SETUP.md 파일을 읽고 "세팅 지침" 섹션의 내용을 그대로 실행해줘. GITHUB_TOKEN 값은 YOUR_GITHUB_TOKEN 으로 설정해줘.
```

---

## 세팅 지침

이 프로젝트(mail-assist-rag)의 로컬 개발 환경을 세팅해줘. 아래 순서대로 진행해:

### 0. 사전 요구사항 확인 및 설치

- Python 3.11+ 가 설치되어 있는지 확인 (`python --version` 또는 `python3 --version`)
- Node.js 18+ 가 설치되어 있는지 확인 (`node --version`)
- 둘 중 하나라도 없거나 버전이 낮으면 자동으로 설치해줘:
  - **Windows**: `winget install Python.Python.3.13 && winget install OpenJS.NodeJS.LTS`
  - **macOS**: `brew install python@3.13 node`
  - **Linux (Ubuntu/Debian)**: `sudo apt update && sudo apt install -y python3 python3-venv nodejs npm`
- 설치 후 python, node 명령이 동작하는지 다시 확인해줘.

### 1. 환경 변수 (.env 파일 생성)

프로젝트 루트에 `.env` 파일을 생성:

```
GITHUB_TOKEN=YOUR_GITHUB_TOKEN
MODEL_NAME=openai/gpt-5-mini
EMBEDDING_MODEL=openai/text-embedding-3-small
DB_PATH=mail_assistant.db
CHROMA_PATH=chroma_data
```

### 2. 백엔드 세팅 (backend/ 디렉토리)

- `python -m venv .venv` 으로 가상환경 생성
- 가상환경 활성화 후 `pip install -r requirements.txt && pip install pydantic-settings`

### 3. 프론트엔드 세팅 (frontend/ 디렉토리)

- `npm install`

### 4. 서버 실행

프로젝트 루트에서 실행:

```bash
python run.py
```

또는 각각 실행:
- **백엔드**: 프로젝트 루트에서 `uvicorn backend.main:app --port 8000`
- **프론트엔드**: frontend/ 디렉토리에서 `npx vite --port 5173`

### 5. 동작 확인

- http://localhost:8000/api/categories 에 접속해서 백엔드 정상 동작 확인
- http://localhost:5173 에 접속해서 프론트엔드 정상 동작 확인

---

## 트러블슈팅

| 증상 | 해결 |
|---|---|
| SSL 인증서 오류 (`CERTIFICATE_VERIFY_FAILED`) | `.env`에 `SSL_VERIFY=false` 추가 |
| `chromadb` 설치 오래 걸림 | C++ 빌드 포함 — 수 분 소요 정상 |
| `pip install` 실패 | venv 활성화 상태인지 확인 |
