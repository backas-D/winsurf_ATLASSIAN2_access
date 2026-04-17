# ATLASSIAN2_access 프로젝트 문서

## 문서 목적

이 문서는 `ATLASSIAN2_access` 프로젝트의 **실제 구현 구조**를 정확히 반영한 기술 문서입니다.  
프로젝트의 아키텍처, 구현된 기능, 파일 구조, 환경 설정, 배포 방법을 명확히 정의하여 신규 개발자가 즉시 이해하고 작업할 수 있도록 합니다.

---

## 1. 프로젝트 개요

### 1.1 프로젝트 소개

`ATLASSIAN2_access`는 Atlassian 제품군(Jira, Confluence)과 연동하는 Flask 기반 웹 애플리케이션입니다.

**주요 목적:**
- 웹 UI를 통한 Jira 이슈 조회, 생성, 수정
- 웹 UI를 통한 Confluence 페이지 조회, 수정, 파일 업로드
- 프로젝트 기반 검색 및 트리 구조 탐색
- 직관적인 사용자 인터페이스 제공

### 1.2 주요 기능

#### Confluence 기능
- **페이지 검색**: 프로젝트/스페이스 이름으로 페이지 검색
- **트리 구조 조회**: 하위 페이지 계층 구조 표시
- **페이지 수정**: 기존 페이지에 내용 추가
- **파일 업로드**: 페이지에 첨부 파일 업로드

#### Jira 기능
- **이슈 검색**: 프로젝트 Key로 이슈 목록 조회
- **이슈 생성**: 새로운 Jira 이슈 생성
- **이슈 수정**: 기존 이슈의 요약/설명 수정
- **이슈 상세**: 상태, 담당자, 타입 등 표시

#### 웹 UI
- **사이드바**: 프로젝트 입력, 검색 버튼
- **메인 영역**: 검색 결과 표시, 트리 구조 탐색
- **상세 패널**: 선택한 항목의 상세 정보
- **액션 버튼**: 수정, 업로드, 생성 등

### 1.3 기술 스택

**백엔드:**
- Python 3.13
- Flask 3.1.0
- Waitress 2.1.2+ (프로덕션 WSGI 서버)
- python-dotenv 1.0.0+ (환경 변수 관리)
- SQLite (로컬 데이터 저장)

**프론트엔드:**
- HTML5
- CSS3
- Vanilla JavaScript
- Flask Jinja2 템플릿

**외부 연동:**
- Atlassian REST API (Jira, Confluence)
- urllib (HTTP 클라이언트)

**개발/배포:**
- Windows Batch Script
- PowerShell
- Git

---

## 2. 시스템 아키텍처

### 2.1 전체 구조

```
┌─────────────┐
│   Browser   │
│  (사용자)    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────────────────────┐
│     Flask Web Server        │
│  ┌─────────┬──────────────┐ │
│  │ main.py │ frontend.py  │ │
│  │         │ (routes)     │ │
│  └────┬────┴──────┬───────┘ │
│       │           │          │
│       ▼           ▼          │
│  ┌────────────────────────┐ │
│  │     backend.py         │ │
│  │  (비즈니스 로직)        │ │
│  └───────┬────────────────┘ │
└──────────┼──────────────────┘
           │ urllib
           ▼
    ┌──────────────┐
    │  Atlassian   │
    │  REST API    │
    │ (Jira/Conf)  │
    └──────────────┘
```

### 2.2 데이터 흐름

1. **사용자 요청**: 브라우저에서 폼 제출 또는 버튼 클릭
2. **Flask 라우팅**: `frontend.py`의 라우트 함수가 요청 수신
3. **비즈니스 로직**: `backend.py`의 함수 호출
4. **API 호출**: urllib로 Atlassian REST API 직접 호출
5. **응답 처리**: JSON 파싱 및 데이터 가공
6. **UI 렌더링**: Jinja2 템플릿으로 HTML 생성
7. **브라우저 표시**: 결과를 사용자에게 표시

### 2.3 핵심 설계 원칙

- **단순성**: 3개 파일 구조로 명확한 역할 분리
- **직접성**: 중간 계층 없이 REST API 직접 호출
- **보안성**: 환경 변수로 인증 정보 관리
- **확장성**: 향후 기능 추가를 위한 구조 유지

---

## 3. 파일 구조 및 역할

### 3.1 실제 디렉터리 구조

```
ATLASSIAN2_access/
├── main.py                         # Flask 앱 진입점
├── frontend.py                     # 라우트 정의
├── backend.py                      # 비즈니스 로직 및 API 호출
├── requirements.txt                # Python 의존성
├── .env                            # 환경 변수 (gitignore)
├── .env.production.example         # 환경 변수 템플릿
├── .gitignore                      # Git 제외 목록
├── project_data.db                 # SQLite 데이터베이스
├── mcp_config.json                 # MCP 설정 (향후 사용)
│
├── templates/                      # HTML 템플릿
│   └── index.html                  # 메인 UI
│
├── static/                         # 정적 파일
│   └── styles.css                  # CSS 스타일
│
├── Data/                           # 업로드 파일 저장
├── logs/                           # 로그 파일 (자동 생성)
│   ├── app.log                     # 애플리케이션 로그
│   ├── error.log                   # 에러 로그
│   └── production_*.log            # 프로덕션 서버 로그
│
├── dist/                           # 배포 패키지 (자동 생성)
├── .venv/                          # Python 가상환경
├── .tmp/                           # 임시 파일
├── __pycache__/                    # Python 캐시
│
├── Run_app.bat                     # 개발 모드 실행
├── Run_production.bat              # 프로덕션 모드 실행
├── setup_firewall.ps1              # 방화벽 설정
├── create_distribution_package.ps1 # 배포 패키지 생성
│
├── README.md                       # ALM MCP 사용 가이드
├── QUICKSTART.md                   # 빠른 시작 가이드
├── DEPLOYMENT.md                   # 상세 배포 가이드
├── DEPLOYMENT_STATUS.md            # 배포 상태 보고서
├── DEPLOYMENT_SUMMARY.md           # 배포 요약
├── ENV_SETUP_GUIDE.md              # 환경 설정 가이드
├── DISTRIBUTION_GUIDE.md           # 배포 패키지 가이드
└── project_access.md               # 본 문서
```

### 3.2 핵심 파일 역할

#### main.py
**역할**: Flask 애플리케이션 생성 및 설정

**주요 기능**:
- Flask 앱 팩토리 패턴 구현
- 환경 변수 로드 (dotenv)
- SECRET_KEY 설정
- 개발/프로덕션 모드 분기
- 로깅 시스템 설정
- 보안 헤더 추가
- Blueprint 등록

**핵심 코드**:
```python
def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    
    is_production = os.getenv("FLASK_ENV") == "production"
    if is_production:
        setup_logging(app)
    
    app.register_blueprint(frontend_bp)
    app.register_blueprint(backend_bp)
    
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
    
    return app
```

#### frontend.py
**역할**: HTTP 라우트 정의 및 요청 처리

**주요 라우트**:
- `GET /`: 메인 페이지
- `POST /search/confluence`: Confluence 페이지 검색
- `POST /search/jira`: Jira 이슈 검색
- `POST /jira/create`: Jira 이슈 생성
- `POST /jira/update`: Jira 이슈 수정
- `POST /confluence/update`: Confluence 페이지 수정
- `POST /confluence/upload`: Confluence 파일 업로드
- `POST /training/generate`: 학습 데이터 생성

**처리 흐름**:
1. 폼 데이터 수신
2. backend 함수 호출
3. 결과를 SearchState에 저장
4. 템플릿 렌더링

#### backend.py
**역할**: 비즈니스 로직 및 Atlassian API 호출

**주요 기능**:
- 환경 변수 로드 및 설정 관리
- SQLite 데이터베이스 관리
- Jira REST API 호출
  - 이슈 검색 (JQL)
  - 이슈 생성
  - 이슈 수정
- Confluence REST API 호출
  - 페이지 검색 (CQL)
  - 페이지 트리 조회
  - 페이지 수정
  - 파일 업로드
- HTTP 요청 헬퍼 함수 (urllib 기반)
- 데이터 모델 정의 (dataclass)

**핵심 데이터 모델**:
```python
@dataclass
class AppConfig:
    openai_api_key: str
    openai_model: str
    jira_base_url: str
    jira_pat: str
    confluence_base_url: str
    confluence_pat: str

@dataclass
class ConfluenceNode:
    id: str
    title: str
    url: str
    children: list["ConfluenceNode"]

@dataclass
class JiraIssue:
    key: str
    summary: str
    status: str
    issue_type: str
    assignee: str
    url: str
```

---

## 4. 주요 기능 상세

### 4.1 Confluence 기능

#### 페이지 검색
**함수**: `find_confluence_pages(project_name, cfg)`

**동작**:
1. 프로젝트 이름으로 CQL 쿼리 생성
2. Confluence REST API `/rest/api/content/search` 호출
3. 검색 결과를 점수화하여 정렬
4. 최상위 페이지 선택
5. 하위 페이지 재귀 조회
6. 트리 구조 생성

**반환**: `list[dict]` (id, title, url, children)

#### 페이지 수정
**함수**: `confluence_update_page(page_id, append_text, title, cfg)`

**동작**:
1. 현재 페이지 내용 조회
2. 기존 내용에 새 텍스트 추가
3. 버전 번호 증가
4. PUT 요청으로 페이지 업데이트

#### 파일 업로드
**함수**: `confluence_upload_attachment(page_id, file, cfg)`

**동작**:
1. 파일명 안전화 (secure_filename)
2. multipart/form-data 생성
3. POST 요청으로 첨부파일 업로드

### 4.2 Jira 기능

#### 이슈 검색
**함수**: `find_jira_issues(project_name, cfg)`

**동작**:
1. 프로젝트 Key 후보 생성
2. JQL 쿼리 생성: `project = KEY ORDER BY updated DESC`
3. Jira REST API `/rest/api/2/search` 호출
4. 이슈 목록 파싱
5. JiraIssue 객체 리스트 반환

**반환**: `list[dict]` (key, summary, status, type, assignee, url)

#### 이슈 생성
**함수**: `jira_create_issue(project_key, issue_type, summary, description, cfg)`

**동작**:
1. 이슈 생성 페이로드 구성
2. POST 요청으로 이슈 생성
3. 생성된 이슈 정보 반환

#### 이슈 수정
**함수**: `jira_update_issue(issue_key, summary, description, cfg)`

**동작**:
1. 수정 페이로드 구성
2. PUT 요청으로 이슈 업데이트

### 4.3 웹 UI 구조

#### 레이아웃
- **사이드바** (좌측):
  - 프로젝트 이름 입력창
  - Confluence 검색 버튼
  - Jira 검색 버튼
  - 최근 활동 목록

- **메인 영역** (중앙):
  - Confluence 페이지 트리
  - Jira 이슈 목록
  - 상세 정보 패널
  - 액션 폼 (생성, 수정, 업로드)

#### 사용자 시나리오

**시나리오 1: Confluence 페이지 찾기**
1. 프로젝트 이름 입력 (예: "IDA")
2. "Confluence 페이지 검색" 버튼 클릭
3. 트리 구조로 페이지 목록 표시
4. 페이지 클릭 시 브라우저에서 열기

**시나리오 2: Jira 이슈 조회**
1. 프로젝트 Key 입력 (예: "IDA")
2. "Jira 이슈 검색" 버튼 클릭
3. 이슈 목록 테이블 표시
4. 이슈 클릭 시 Jira 웹에서 열기

**시나리오 3: Confluence 페이지 수정**
1. 페이지 검색 후 선택
2. 추가할 내용 입력
3. "페이지 수정" 버튼 클릭
4. 성공 메시지 확인

---

## 5. 환경 설정

### 5.1 필수 요구사항

**시스템**:
- Windows 10/11 또는 Windows Server 2016+
- Python 3.12 이상 (3.13 권장)
- 인터넷 연결

**선택사항**:
- Node.js 18+ (MCP 서버 사용 시)

### 5.2 환경 변수

`.env` 파일에 다음 변수를 설정해야 합니다:

#### 필수 변수

```bash
# Flask 설정
FLASK_ENV=production
SECRET_KEY=<생성된-비밀키>

# Jira 설정
JIRA_BASE_URL=https://jira.your-company.com
JIRA_PAT=<your-jira-personal-access-token>

# Confluence 설정
CONFLUENCE_BASE_URL=https://confluence.your-company.com
CONFLUENCE_PAT=<your-confluence-personal-access-token>
```

#### 선택 변수

```bash
# OpenAI (향후 Chat Bot 기능용)
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=gpt-5.4

# MCP 서버 (향후 사용)
ALM_MCP_STDIO_PATH=C:\Tools\alm-mcp-stdio\dist\index.js
```

### 5.3 PAT 생성 방법

#### Jira PAT
1. Jira 로그인
2. Profile → Personal Access Tokens
3. Create Token
4. 토큰 복사 후 `.env`에 입력

#### Confluence PAT
1. Confluence 로그인
2. 환경설정 → 개인용 액세스 토큰
3. 토큰 만들기
4. 토큰 복사 후 `.env`에 입력

### 5.4 의존성 설치

**requirements.txt**:
```
Flask==3.1.0
extract-msg==0.55.0
openai>=1.0.0
waitress>=2.1.2
python-dotenv>=1.0.0
```

**설치 명령**:
```bash
pip install -r requirements.txt
```

---

## 6. 실행 방법

### 6.1 개발 모드

**실행**:
```bash
Run_app.bat
```

**특징**:
- 로컬호스트만 접근 가능 (127.0.0.1:5000)
- Debug 모드 활성화
- 코드 변경 시 자동 재시작
- 상세 에러 메시지 표시
- 브라우저 자동 실행

**접속**:
- http://127.0.0.1:5000

### 6.2 프로덕션 모드

**실행**:
```bash
Run_production.bat
```

**특징**:
- 외부 접근 허용 (0.0.0.0:5000)
- Waitress WSGI 서버 사용
- 멀티스레드 (4 threads)
- 로그 파일 자동 생성
- 보안 헤더 적용
- 브라우저 자동 실행

**접속**:
- 로컬: http://127.0.0.1:5000
- 내부 네트워크: http://[서버-IP]:5000
- 외부 인터넷: http://[공인-IP]:5000 (포트 포워딩 필요)

### 6.3 방화벽 설정

외부 접근을 허용하려면 Windows 방화벽 설정이 필요합니다.

**PowerShell 관리자 권한으로 실행**:
```powershell
cd "d:\Work\02.Project\140. AItool\ATLASSIAN2_access"
PowerShell -ExecutionPolicy Bypass -File .\setup_firewall.ps1
```

**수동 설정**:
```powershell
New-NetFirewallRule -DisplayName "ATLASSIAN2 Access - Port 5000" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5000 `
    -Action Allow `
    -Profile Domain,Private,Public
```

---

## 7. 배포 가이드

### 7.1 배포 패키지 생성

**자동 생성**:
```powershell
PowerShell -ExecutionPolicy Bypass -File .\create_distribution_package.ps1 -Version "1.0.0"
```

**생성 결과**:
- `dist\ATLASSIAN2_Access_v1.0.0.zip`

**포함 파일**:
- 애플리케이션 소스 코드
- 실행 스크립트
- 환경 변수 템플릿
- 설치 가이드 (자동 생성)
- 문서

**제외 파일** (보안):
- `.env` (실제 API 키)
- `logs/` (로그 파일)
- `project_data.db` (데이터베이스)
- `.venv/` (가상환경)

### 7.2 사용자 배포

**배포 절차**:
1. ZIP 파일 전달
2. 사용자가 압축 해제
3. `.env.production.example`을 `.env`로 복사
4. `.env` 파일 수정 (SECRET_KEY, PAT 입력)
5. `Run_production.bat` 실행

**사용자 안내 사항**:
- Python 3.12+ 설치 필요
- 각자의 PAT 발급 필요
- SECRET_KEY 생성 필요
- 방화벽 설정 (외부 접근 시)

### 7.3 GitHub 저장소

**저장소 정보**:
- **URL**: https://github.com/backas-D/winsurf_ATLASSIAN2_access
- **소유자**: backas-D
- **이메일**: hyuckmin@gmail.com
- **브랜치**: main

**저장소 내용**:
- 전체 소스 코드
- 배포 스크립트
- 문서
- 배포 패키지 (dist/)

---

## 8. 보안 및 운영

### 8.1 보안 정책

#### 인증 정보 관리
- **저장 위치**: `.env` 파일만
- **Git 제외**: `.gitignore`에 `.env` 포함
- **공유 금지**: PAT, API Key 절대 외부 공유 금지
- **정기 갱신**: PAT 정기적으로 재발급

#### 보안 헤더
```python
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
```

#### SECRET_KEY 생성
```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

### 8.2 로깅 시스템

#### 로그 파일
- **app.log**: 일반 애플리케이션 로그 (INFO 레벨)
- **error.log**: 에러 로그 (ERROR 레벨)
- **production_*.log**: 프로덕션 서버 로그

#### 로그 로테이션
- 최대 파일 크기: 10MB
- 백업 파일 수: 10개
- 자동 압축 및 순환

#### 로그 확인
```powershell
# 실시간 모니터링
Get-Content logs\app.log -Wait

# 최근 로그 확인
Get-Content logs\app.log -Tail 50

# 에러 로그 확인
Get-Content logs\error.log -Tail 20
```

### 8.3 모니터링

#### 연결 상태 확인
- Jira API 연결
- Confluence API 연결
- 데이터베이스 연결

#### 성능 모니터링
- 응답 시간
- 에러 발생률
- 동시 접속자 수

---

## 9. 향후 개선 계획

### 9.1 Chat Bot 기능 추가

**목표**: 자연어 기반 Jira/Confluence 작업 처리

**구현 계획**:
- OpenAI `gpt-5-mini` 모델 연동
- 사용자 의도 분석
- 적절한 API 호출 자동 선택
- 자연어 응답 생성
- 대화 이력 관리

**UI 추가**:
- Chat Bot 탭
- 메시지 입력창
- 대화 이력 표시
- 실행 결과 요약

### 9.2 MCP 서버 연동

**목표**: ALM MCP stdio 서버를 통한 통합 API 호출

**구현 계획**:
- Node.js MCP 서버 연동
- stdio 프로토콜 구현
- 기존 직접 API 호출을 MCP 호출로 전환
- Tool 기반 작업 처리

**장점**:
- 통합된 API 인터페이스
- 표준화된 요청/응답
- 확장 가능한 구조

### 9.3 모듈 구조 개선

**목표**: 유지보수성 향상을 위한 구조 개선

**제안 구조**:
```
app/
├── __init__.py
├── routes/
│   ├── web.py
│   ├── jira.py
│   ├── confluence.py
│   └── chat.py
├── services/
│   ├── jira_service.py
│   ├── confluence_service.py
│   └── chat_service.py
├── repositories/
│   ├── log_repository.py
│   └── history_repository.py
└── models/
    ├── config.py
    ├── jira.py
    └── confluence.py
```

**장점**:
- 명확한 계층 분리
- 테스트 용이성
- 기능 확장 용이

### 9.4 추가 기능

- **검색 필터**: 날짜, 상태, 담당자 등
- **즐겨찾기**: 자주 사용하는 프로젝트/페이지
- **최근 이력**: 검색 및 작업 이력
- **대시보드**: 통계 및 요약 정보
- **알림**: 이슈 변경, 댓글 등
- **다국어 지원**: 영어, 한국어

---

## 10. 개선 이력

### v1.1.0 - 2026-04-07 (문서 재구성)

#### 10.1 문서 전면 재작성
- **실제 구현 기반**: 현재 코드 구조를 정확히 반영
- **명확한 구분**: 구현 완료 vs 향후 계획 분리
- **상세 설명**: 각 파일 역할 및 함수 동작 설명
- **실용성 향상**: 신규 개발자가 즉시 이해 가능한 수준

#### 10.2 주요 변경 사항
- Chat Bot 기능을 "향후 개선 계획"으로 이동 (미구현)
- MCP 서버 연동을 "향후 개선 계획"으로 이동 (미구현)
- 실제 3파일 구조 (main.py, frontend.py, backend.py) 명확화
- urllib 기반 직접 REST API 호출 방식 설명
- GitHub 저장소 정보 추가

#### 10.3 문서 구조 개선
- 10개 섹션으로 체계적 재구성
- 실제 파일 구조 및 역할 상세 설명
- 데이터 흐름 다이어그램 추가
- 사용자 시나리오 예시 추가
- 배포 가이드 통합

---

### v1.0.0 - 2026-03-31 (프로덕션 배포 구성)

#### 10.4 프로덕션 배포 환경 구축
- **Waitress WSGI 서버 도입**
  - Windows 환경 최적화
  - 멀티스레드 지원 (4 threads)
  - 외부 접근 허용 (0.0.0.0:5000)

- **프로덕션 실행 스크립트**
  - `Run_production.bat` 생성
  - 자동 의존성 설치
  - 로그 파일 자동 생성
  - 웹브라우저 자동 실행

#### 10.5 보안 강화
- **환경별 설정 분리**
  - 개발/프로덕션 모드 분리
  - SECRET_KEY 환경 변수 관리
  - `.env.production.example` 템플릿

- **보안 헤더 추가**
  - X-Content-Type-Options
  - X-Frame-Options
  - X-XSS-Protection

- **환경 변수 관리**
  - python-dotenv 라이브러리
  - SECRET_KEY 자동 생성 가이드
  - API 키 보안 관리

#### 10.6 로깅 시스템 구축
- **자동 로그 로테이션**
  - app.log (애플리케이션)
  - error.log (에러)
  - production_*.log (서버)
  - 최대 10MB, 10개 백업

- **로그 레벨 관리**
  - 프로덕션: INFO
  - 개발: DEBUG
  - 에러 로그 분리

#### 10.7 네트워크 및 방화벽
- **Windows 방화벽 스크립트**
  - `setup_firewall.ps1` 생성
  - 포트 5000 자동 개방
  - IP 범위 제한 옵션
  - 관리자 권한 확인

- **외부 접근 지원**
  - 로컬호스트
  - 내부 네트워크
  - 외부 인터넷 (포트 포워딩)

#### 10.8 배포 문서화
- **상세 가이드**
  - DEPLOYMENT.md
  - QUICKSTART.md (8분 완료)
  - ENV_SETUP_GUIDE.md
  - DEPLOYMENT_STATUS.md
  - DEPLOYMENT_SUMMARY.md

- **트러블슈팅**
  - 일반 문제 해결
  - API 연결 실패
  - 방화벽 설정
  - 로그 확인

#### 10.9 배포 패키지 자동화
- **패키지 생성 스크립트**
  - `create_distribution_package.ps1`
  - 필요 파일 자동 선별
  - 민감 정보 제외
  - ZIP 자동 생성

- **배포 패키지 구성**
  - 소스 코드
  - 실행 스크립트
  - 환경 변수 템플릿
  - INSTALL.md (자동 생성)
  - version.json

- **배포 가이드**
  - DISTRIBUTION_GUIDE.md
  - 사용자별 설정 방법
  - 보안 주의사항
  - 버전 관리

#### 10.10 GitHub 저장소
- **저장소 생성 및 초기 커밋**
  - 저장소: backas-D/winsurf_ATLASSIAN2_access
  - 브랜치: main
  - 34개 파일, 3,843줄 추가

#### 10.11 배포 완료 상태
- ✅ 프로덕션 서버 구성 완료
- ✅ 보안 설정 완료
- ✅ 로깅 시스템 구축 완료
- ✅ 배포 문서화 완료
- ✅ 배포 패키지 자동화 완료
- ✅ 외부 접근 지원 완료
- ✅ GitHub 저장소 생성 완료
- ⚠️ 사용자별 API 키 설정 필요
- ⚠️ 방화벽 설정 필요 (관리자 권한)
- ⚠️ HTTPS 설정 권장 (프로덕션 환경)

---

## 부록

### A. 참고 문서
- `README.md`: ALM MCP 사용 가이드
- `QUICKSTART.md`: 빠른 시작 가이드
- `DEPLOYMENT.md`: 상세 배포 가이드
- `ENV_SETUP_GUIDE.md`: 환경 설정 가이드
- `DISTRIBUTION_GUIDE.md`: 배포 패키지 가이드

### B. 외부 링크
- GitHub 저장소: https://github.com/backas-D/winsurf_ATLASSIAN2_access
- Jira REST API: https://docs.atlassian.com/jira/REST/
- Confluence REST API: https://docs.atlassian.com/confluence/REST/

### C. 문서 관리 규칙
- 추가 내용은 직전 개선확인 이후 새롭게 변경된 사항만 반영
- 추가 기록에는 반드시 버전과 날짜 표시
- 버전 표기: `v{major}.{minor}.{patch} - YYYY-MM-DD`
- 개선확인으로 추가되는 내용은 누적 기록 방식으로 관리
- **개선확인** 프롬프트 시 현재 기준 개선 사항을 이 파일에 추가

---

### v1.2.0 - 2026-04-08 (OEM 기반 프로젝트 선택 시스템)

#### 10.12 OEM 선택 및 프로젝트 모달 시스템 구축

**목표**: Confluence 검색 방식을 OEM 루트 기반 프로젝트 선택으로 전환

**구현 내용**:

1. **OEM 선택 드롭다운 추가**
   - 사이드바에 OEM 선택 UI 추가
   - 지원 OEM: KGM (Default), HMC, KMC, Genesis, STLA
   - 자동 OEM 감지 기능 (프로젝트 코드 기반)

2. **OEM 루트 페이지 매핑**
   ```python
   OEM_ROOT_PAGES = {
       "KGM": "53087142",      # KGM+SYMC PJT
       "HMC": "48627901",      # HYUNDAI Vehicle Dev. - Design Korea
       "KMC": "330446288",     # KIA Vehicle Dev. - Design Korea
       "Genesis": "330446292", # GENESIS Vehicle Dev. - Design Korea
       "STLA": "231411537"     # STLA Vehicle Dev.
   }
   ```

3. **프로젝트 선택 모달 구현**
   - OEM 선택 후 "Confluence 페이지 검색" 버튼 클릭 시 모달 표시
   - 각 OEM 루트의 하위 프로젝트 목록 자동 로드
   - 실시간 필터링 기능 (프로젝트 이름 검색)
   - 프로젝트 클릭 시 해당 프로젝트 트리 구조 자동 로드

4. **OEM별 프로젝트 추출 로직**

   **KGM (특별 처리)**:
   - 재귀적 하위 디렉토리 탐색 (최대 3단계)
   - 프로젝트 코드 패턴 필터링: `[ACEJOQUXY] + 숫자`
   - "Complete PJT - SYMC" 하위 프로젝트 포함
   - 제외 키워드: DAILY, TASK, REPORT, MEETING, REVIEW, TEMPLATE, REQUIREMENT, SAMPLE
   - 한글 포함 항목 자동 제외
   
   **지원 프로젝트 예시**:
   - Q270, Y470, U100, U101, C330, J115, J120, X180, E130, O100, J140, J145, Q300, J150
   - A200, C300, E100, FCM-20 Q200, FCM-20 X150, X170, Q250, Y450, J100, Q261, Y461

   **HMC, KMC, Genesis, STLA (단순 처리)**:
   - 루트 페이지의 직접 하위 페이지만 가져오기
   - 필터링 없이 모든 페이지 표시
   - 전체 제목 그대로 표시

5. **API 엔드포인트 추가**
   - `GET /api/oem-projects/<oem>`: OEM 프로젝트 목록 조회
   - `POST /api/load-project-tree`: 선택한 프로젝트 트리 로드

6. **UI/UX 개선**
   - 모달 창 애니메이션 및 스타일링
   - 검색 입력창 제거 (OEM 선택 → 모달 방식으로 단순화)
   - 프로젝트 목록 정렬 (알파벳순)
   - 로딩 상태 표시

#### 10.13 프로젝트 코드 패턴 확장

**KGM 프로젝트 코드 검증 강화**:
```python
patterns = [
    r'^[ACEJOQUXY]\d{2,4}[,\s]',           # Q270, Y470, U100, A200, X180
    r'^[ACEJOQUXY]\d{2,4}\s*\[',           # J115 [FCM-30W, MRR-35]
    r'^FCM-\d+\s+[ACEJOQUXY]\d{2,4}',      # FCM-20 Q200, FCM-20 X150
    r'^[ACEJOQUXY]\d{2,4}\s+[ACEJOQUXY]\d{2,4}',  # U100, U101
]
```

**추가된 문자**:
- A (A200 프로젝트 지원)
- 기존: E, C, J, O, Q, U, X, Y

**제외 로직**:
- 한글 문자 포함 항목 자동 제외 (ASCII만 허용)
- 키워드 기반 제외: DAILY, TASK, REPORT, MEETING, REVIEW, TEMPLATE, REQUIREMENT, SAMPLE

#### 10.14 기술적 개선 사항

**백엔드 함수 추가**:
- `get_oem_projects()`: OEM별 프로젝트 목록 추출
- `is_kgm_project_code()`: KGM 프로젝트 코드 검증
- `find_related_projects()`: 관련 프로젝트 자동 감지
- `detect_oem_from_project_code()`: 프로젝트 코드로 OEM 자동 감지

**프론트엔드 기능 추가**:
- `showOEMProjectSelector()`: OEM 프로젝트 선택 모달 표시
- `loadOEMProjects()`: OEM 프로젝트 목록 로드
- `renderProjectList()`: 프로젝트 목록 렌더링
- `filterProjects()`: 실시간 프로젝트 필터링
- `selectOEMProject()`: 프로젝트 선택 및 트리 로드

**CSS 스타일 추가**:
- `.oem-selector`: OEM 선택 드롭다운 스타일
- `.modal`: 모달 창 스타일 및 애니메이션
- `.project-list`: 프로젝트 목록 스타일
- `.search-box`: 검색 입력창 스타일

#### 10.15 사용자 워크플로우 개선

**새로운 검색 프로세스**:
```
1. OEM 선택 (KGM, HMC, KMC, Genesis, STLA)
   ↓
2. "Confluence 페이지 검색" 버튼 클릭
   ↓
3. 프로젝트 선택 모달 표시
   - OEM 루트의 프로젝트 목록 자동 로드
   - 실시간 필터링 가능
   ↓
4. 원하는 프로젝트 클릭
   ↓
5. 프로젝트 트리 구조 자동 표시
   - 하위 페이지 계층 구조
   - 페이지 클릭으로 Confluence 이동
```

**이전 방식과 비교**:
- **Before**: 프로젝트 이름 직접 입력 → 검색 → 트리 표시
- **After**: OEM 선택 → 프로젝트 목록에서 선택 → 트리 표시

**장점**:
- 프로젝트 이름을 정확히 몰라도 탐색 가능
- OEM별 구조화된 프로젝트 관리
- 오타 방지 및 사용자 편의성 향상
- 전체 프로젝트 목록 파악 용이

#### 10.16 배포 영향

**변경된 파일**:
- `backend.py`: OEM 루트 매핑, 프로젝트 추출 로직
- `frontend.py`: API 엔드포인트 추가
- `templates/index.html`: OEM 선택 UI, 프로젝트 모달
- `static/styles.css`: 모달 및 OEM 선택 스타일

**호환성**:
- 기존 Jira 검색 기능은 변경 없음
- 기존 Confluence 페이지 수정/업로드 기능 유지
- 환경 변수 변경 없음

**업그레이드 방법**:
1. 최신 코드 pull
2. 서버 재시작
3. 브라우저 캐시 클리어
4. 새로운 OEM 선택 UI 확인

---

## 11. v1.3.0 개선사항 (2026-04-08)

### 11.1 Quill.js 리치 텍스트 에디터 도입

#### 11.1.1 기존 문제점
- 일반 textarea로는 텍스트 서식 지정 불가
- 이미지 삽입 불가능
- 제한적인 편집 기능

#### 11.1.2 Quill.js 에디터 구현

**추가된 라이브러리**:
```html
<link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
<script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
```

**에디터 기능**:
- **텍스트 서식**: 굵게, 기울임, 밑줄
- **폰트 크기**: Small (0.75em), Normal (1em), Large (1.5em), Huge (2em)
- **리스트**: 순서 있는 리스트, 순서 없는 리스트
- **이미지 삽입**: 파일 선택 또는 클립보드 붙여넣기 (Ctrl+V)
- **서식 지우기**: Clean 버튼

**에디터 초기화**:
```javascript
var quill = new Quill('#quill_editor', {
  theme: 'snow',
  placeholder: '[Software Release Note] 밑에 작성할 내용을 입력하세요.',
  modules: {
    toolbar: [
      [{ 'size': ['small', false, 'large', 'huge'] }],
      ['bold', 'italic', 'underline'],
      [{ 'list': 'ordered'}, { 'list': 'bullet' }],
      ['image'],
      ['clean']
    ]
  }
});
```

### 11.2 이미지 자동 압축 및 업로드

#### 11.2.1 이미지 압축 기능

**문제**: Base64 이미지가 너무 커서 "Request Entity Too Large" 오류 발생

**해결**: 클라이언트 측 자동 압축
```javascript
function compressImage(file, maxWidth, maxHeight, quality) {
  // 1. Canvas에 이미지 그리기
  // 2. 최대 크기 제한 (800x600)
  // 3. JPEG로 압축 (품질 70%)
  // 4. Base64 반환
}
```

**압축 설정**:
- 최대 너비: 800px
- 최대 높이: 600px
- 압축 품질: 70%
- 출력 포맷: JPEG

**효과**:
- Before: 1920x1080 스크린샷 → 2-3MB Base64 → 413 오류
- After: 800x450 압축 이미지 → 100-200KB Base64 → 정상 전송 ✅

#### 11.2.2 Confluence 첨부 파일 변환

**문제**: Confluence는 Base64 이미지를 직접 표시하지 못함

**해결**: Base64 → Confluence 첨부 파일 자동 변환
```python
def upload_base64_image_to_confluence(page_id, base64_data, image_index, cfg):
    # 1. Base64 디코딩
    image_binary = base64.b64decode(base64_data)
    
    # 2. 고유 파일명 생성
    filename = f"image_{timestamp}_{image_index}.jpg"
    
    # 3. Confluence 첨부 파일로 업로드
    confluence_upload_attachment(page_id, file_storage, cfg)
    
    # 4. Confluence 이미지 매크로 반환
    return '<p><ac:image><ri:attachment ri:filename="..."/></ac:image></p>'
```

**변환 과정**:
```
Quill 에디터 (Base64)
    ↓
<img src="data:image/jpeg;base64,/9j/4AAQ...">
    ↓
첨부 파일 업로드 (image_20260408_140821_1.jpg)
    ↓
<ac:image><ri:attachment ri:filename="image_20260408_140821_1.jpg"/></ac:image>
    ↓
Confluence 페이지에 이미지 표시 ✅
```

### 11.3 스마트 콘텐츠 삽입 위치

#### 11.3.1 우선순위 기반 삽입 로직

**삽입 위치 우선순위**:
1. **[Software Release Note] 섹션 아래** (1순위)
2. **참고사항 매크로 아래** (2순위)
3. **페이지 제목(h1/h2) 아래** (3순위)
4. **페이지 끝** (폴백)

**구현 코드**:
```python
# Priority 1: [Software Release Note] 또는 [SRR] Release Note
markers = ['[Software Release Note]', '[SRR] Release Note']
for marker in markers:
    if marker in current_body:
        insert_pos = find_marker_end(marker)

# Priority 2: 참고사항 매크로
if insert_pos == -1 and '<ac:structured-macro ac:name="info">' in current_body:
    insert_pos = find_macro_end()

# Priority 3: 페이지 제목
if insert_pos == -1:
    insert_pos = find_h1_or_h2_end()
```

**삽입 형식**:
```html
<p><strong>[2026-04-08 14:05:58]</strong></p>
<p>사용자가 입력한 내용 (서식 포함)</p>
<p><ac:image><ri:attachment ri:filename="image_20260408_140558_1.jpg"/></ac:image></p>
```

### 11.4 HTML → Confluence XHTML 변환

#### 11.4.1 XHTML 호환성 처리

**문제**: Quill HTML이 Confluence XHTML 파서와 호환되지 않음

**해결**: HTML Sanitization 함수
```python
def sanitize_html_for_confluence(html, page_id, cfg):
    # 1. Base64 이미지 → 첨부 파일 변환
    html = convert_images_to_attachments(html)
    
    # 2. 폰트 크기 클래스 → 인라인 스타일
    html = convert_font_size_classes(html)
    
    # 3. 빈 paragraph 제거
    html = remove_empty_paragraphs(html)
    
    # 4. Self-closing 태그 정규화
    html = normalize_self_closing_tags(html)
    
    return html
```

#### 11.4.2 폰트 크기 변환

**Quill 출력**:
```html
<span class="ql-size-large">큰 텍스트</span>
```

**Confluence 변환**:
```html
<span style="font-size: 1.5em;">큰 텍스트</span>
```

**크기 매핑**:
- `ql-size-small` → `font-size: 0.75em;`
- (기본값) → (없음)
- `ql-size-large` → `font-size: 1.5em;`
- `ql-size-huge` → `font-size: 2em;`

### 11.5 UI/UX 개선

#### 11.5.1 "새 제목(선택)" 필드 제거

**변경 이유**:
- 제목 변경은 드물게 사용됨
- UI 간소화 필요
- Confluence에서 직접 제목 수정 가능

**변경 사항**:
- `confluence_title` input 필드 제거
- hidden input으로 빈 값 전송 (기존 제목 유지)

#### 11.5.2 Placeholder 텍스트 개선

**Before**: "본문 끝에 덧붙일 내용을 입력하세요"  
**After**: "[Software Release Note] 밑에 작성할 내용을 입력하세요."

**효과**: 사용자가 삽입 위치를 명확히 인지

#### 11.5.3 에디터 스타일링

**CSS 커스터마이징**:
```css
#quill_editor {
  background: var(--paper-strong);
  border-radius: 16px;
}

.ql-toolbar {
  border-radius: 16px 16px 0 0;
  background: rgba(255, 255, 255, 0.5);
}

.ql-container {
  border-radius: 0 0 16px 16px;
}

.ql-editor {
  min-height: 150px;
  font-size: 0.95rem;
}
```

**디자인 일관성**: 기존 UI와 조화로운 둥근 모서리 및 색상

### 11.6 기술적 개선사항

#### 11.6.1 에러 처리 강화

**이미지 업로드 실패 처리**:
```python
try:
    confluence_upload_attachment(page_id, file_storage, cfg)
    return confluence_image_macro
except Exception as e:
    print(f"Failed to upload image: {e}")
    traceback.print_exc()
    return ''  # 이미지 제외하고 계속 진행
```

#### 11.6.2 정규식 패턴 개선

**다양한 HTML 형식 처리**:
```python
# img 태그 (self-closing 및 일반)
html = re.sub(r'<img[^>]*src="(data:image/[^"]+)"[^>]*/?>', replace_image, html)

# br 태그 정규화
html = re.sub(r'<br\s*>', '<br/>', html)

# 빈 paragraph
html = re.sub(r'<p>\s*<br/?\s*>\s*</p>', '', html)
```

### 11.7 변경된 파일 목록

**Frontend**:
- `templates/index.html`
  - Quill.js CDN 추가
  - textarea → Quill 에디터 교체
  - 이미지 압축 JavaScript 추가
  - 폼 제출 시 HTML 변환 로직
  - "새 제목" 필드 제거

**Backend**:
- `backend.py`
  - `upload_base64_image_to_confluence()` 함수 추가
  - `sanitize_html_for_confluence()` 함수 개선
  - 폰트 크기 클래스 → 인라인 스타일 변환
  - 스마트 콘텐츠 삽입 위치 로직

**Styling**:
- `static/styles.css`
  - Quill 에디터 커스텀 스타일
  - 폰트 크기 스타일 정의

### 11.8 사용자 워크플로우

**새로운 콘텐츠 추가 프로세스**:
```
1. Confluence 페이지 검색 및 선택
   ↓
2. Quill 에디터에서 내용 작성
   - 텍스트 서식 적용 (굵게, 기울임, 크기 조정)
   - 이미지 붙여넣기 (Ctrl+V) 또는 파일 선택
   - 리스트 작성
   ↓
3. "Confluence 내용 추가" 버튼 클릭
   ↓
4. 자동 처리
   - 이미지 압축 (800x600, 70%)
   - Base64 → Confluence 첨부 파일 변환
   - 폰트 크기 클래스 → 인라인 스타일
   - HTML → XHTML 변환
   ↓
5. Confluence 페이지 업데이트
   - [Software Release Note] 아래에 삽입
   - 타임스탬프 자동 추가
   - 이미지 정상 표시
```

### 11.9 성능 및 제한사항

**이미지 압축**:
- 장점: 전송 크기 감소, 서버 부하 감소
- 제한: 매우 고해상도 이미지는 품질 저하 가능

**Base64 vs 첨부 파일**:
- Base64 인코딩: 원본 크기의 133%
- 첨부 파일 변환: 추가 API 호출 필요
- 선택: 첨부 파일 방식 (페이지 크기 최소화)

**브라우저 호환성**:
- Quill.js: 모던 브라우저 지원 (IE11 이상)
- Canvas API: 이미지 압축에 필요
- FileReader API: Base64 변환에 필요

### 11.10 배포 및 업그레이드

**변경 사항**:
- 외부 의존성: Quill.js CDN (인터넷 연결 필요)
- 환경 변수: 변경 없음
- 데이터베이스: 변경 없음

**업그레이드 방법**:
1. 최신 코드 pull
2. 서버 재시작
3. 브라우저 캐시 클리어 (Ctrl+F5)
4. Quill 에디터 확인

**호환성**:
- 기존 Jira 기능: 영향 없음
- 기존 Confluence 파일 업로드: 영향 없음
- 기존 페이지 검색: 영향 없음

### 11.11 향후 개선 가능 사항

**고려 중인 기능**:
- [ ] 이미지 크기 조정 (드래그로 리사이즈)
- [ ] 테이블 삽입 기능
- [ ] 코드 블록 하이라이팅
- [ ] 링크 삽입 기능
- [ ] 색상 선택 기능
- [ ] 실시간 미리보기

**기술적 개선**:
- [ ] 이미지 업로드 진행률 표시
- [ ] 오프라인 모드 지원 (LocalStorage)
- [ ] 자동 저장 기능
- [ ] 버전 히스토리

---

---

## 12. v1.3.1 개선사항 (2026-04-08)

### 12.1 파일 첨부 및 다운로드 기능 구현

#### 12.1.1 Quill 에디터 파일 첨부 버튼 (📎)

**구현 내용**:
- Quill 툴바에 📎(클립) 파일 첨부 버튼 추가
- 여러 파일 동시 선택 가능
- 에디터에 파일 정보 자동 삽입: `📎 파일명.ext (123.45 KB)`
- JavaScript `attachedFiles` 배열로 파일 관리
- FormData를 통한 파일 + 텍스트 동시 전송 (fetch API)

**에디터 표시 형식**:
```
📎 RE RE KGM 전방카메라 고장진단 검출 조건 사양 검토 건 (SIW ESC 진단시 ADAS 경고등 미점등) (1).msg (400.50 KB)
```

#### 12.1.2 Confluence 페이지 내 클릭 가능한 다운로드 링크

**구현 방식**: Confluence REST API에서 실제 다운로드 URL을 수집하여 `<a href>` 링크 생성

**처리 흐름**:
```
1. 파일 먼저 Confluence에 업로드
   POST /rest/api/content/{page_id}/child/attachment
   ↓
2. 첨부 파일 목록 API 조회
   GET /rest/api/content/{page_id}/child/attachment?limit=50
   ↓
3. 각 첨부 파일의 다운로드 URL 수집
   attachment['_links']['download']
   예: /download/attachments/411546983/filename.pptx?version=1&modificationDate=...&api=v2
   ↓
4. 에디터 텍스트의 파일명과 퍼지 매칭
   ↓
5. 매칭된 URL로 <a href="..."> 링크 생성 (& → &amp; 이스케이프)
   ↓
6. Confluence 페이지에 클릭 가능한 다운로드 링크 표시 ✅
```

#### 12.1.3 퍼지 파일명 매칭 (핵심 해결책)

**문제**: Confluence가 파일 업로드 시 한글 등 비-ASCII 문자를 제거하여 파일명이 변경됨

```
원본: 260403_주간업무_Design2팀.pptx
Confluence: 260403__Design2.pptx          ← 한글 '주간업무', '팀' 제거

원본: RE RE KGM 전방카메라 고장진단 검출 조건 사양 검토 건 (SIW ESC 진단시 ADAS 경고등 미점등) (1).msg
Confluence: RE_RE_KGM_SIW_ESC_ADAS__1.msg  ← 한글 전부 제거
```

**해결**: 정규화 기반 퍼지 매칭 함수
```python
def normalize_filename(name):
    # 1. 비-ASCII 문자 제거 (한글 등)
    name = re.sub(r'[^\x00-\x7F]', '', name)
    # 2. 영숫자, 마침표 외 모든 문자를 _로 치환
    name = re.sub(r'[^a-zA-Z0-9.]', '_', name)
    # 3. 연속 _ 제거
    name = re.sub(r'_+', '_', name)
    # 4. 마침표 앞뒤 _ 제거 (1_.msg → 1.msg)
    name = re.sub(r'_\.', '.', name)
    name = re.sub(r'\._', '.', name)
    return name.strip('_').lower()
```

**매칭 결과**:
```
260403_주간업무_Design2팀.pptx  →  260403_design2.pptx  ✅ MATCH
260403__Design2.pptx           →  260403_design2.pptx  ✅

RE RE KGM 전방카메라...(1).msg →  re_re_kgm_siw_esc_adas_1.msg  ✅ MATCH
RE_RE_KGM_SIW_ESC_ADAS__1.msg →  re_re_kgm_siw_esc_adas_1.msg  ✅
```

#### 12.1.4 XHTML 호환성 처리

**문제**: Confluence 다운로드 URL에 `&` 문자가 포함되어 XHTML 파싱 오류 발생
```
?version=1&modificationDate=...&api=v2   ← XHTML에서 & 는 유효하지 않음
```

**해결**: `&` → `&amp;` 이스케이프
```python
safe_url = download_url.replace('&', '&amp;')
```

**Confluence 페이지 저장 형식**:
```html
<p><strong>📎 첨부: <a href="https://confluence.hlklemove.com/download/attachments/411546983/
260403__Design2.pptx?version=1&amp;modificationDate=1775629213881&amp;api=v2">
260403_주간업무_Design2팀.pptx</a></strong> (161.23 KB)</p>
```

### 12.2 UI 개선

#### 12.2.1 별도 파일 업로드 폼 제거

**변경 사항**:
- "Confluence 파일 업로드" 별도 섹션 제거 (`/confluence/upload` 폼)
- 파일 첨부는 Quill 에디터의 📎 버튼으로 통합
- 텍스트 + 파일을 하나의 폼에서 동시 처리

**Before**:
```
[Confluence 내용 추가] 폼 + [Confluence 파일 업로드] 폼 (별도)
```

**After**:
```
[Confluence 내용 추가] 폼 (📎 파일 첨부 통합)
```

### 12.3 기술적 개선사항

#### 12.3.1 파일 업로드 순서 변경

**Before (문제)**:
```
1. confluence_update_page() 호출 → HTML에 파일 링크 삽입
2. 파일 업로드 → Confluence에 첨부
→ 문제: 링크 생성 시점에 다운로드 URL을 모름
```

**After (해결)**:
```
1. 파일 먼저 업로드 → Confluence 첨부
2. 첨부 파일 목록 API 조회 → 다운로드 URL 수집
3. confluence_update_page() 호출 → 정확한 URL로 링크 생성
```

#### 12.3.2 시도한 접근법 및 최종 선택

| 접근법 | 결과 | 문제점 |
|--------|------|--------|
| Flask 프록시 다운로드 | ❌ 404 | Confluence 다운로드 URL에 version 파라미터 필요 |
| ac:link 네이티브 링크 | ❌ 클릭 가능하나 안 열림 | Confluence 미리보기로 동작 |
| 직접 URL 구성 | ❌ 404 | 한글 파일명 인코딩 깨짐 |
| **API 다운로드 URL + 퍼지 매칭** | **✅ 성공** | **최종 채택** |

### 12.4 변경된 파일 목록

**Frontend**:
- `frontend.py`
  - 파일 업로드 순서 변경 (업로드 → API 조회 → 페이지 업데이트)
  - 첨부 파일 목록 API 호출 추가 (`requests` 라이브러리 사용)
  - 디버그 로깅 추가

- `templates/index.html`
  - Quill 에디터 📎 파일 첨부 버튼 추가
  - FormData를 통한 파일 전송 JavaScript
  - 별도 파일 업로드 폼 제거

**Backend**:
- `backend.py`
  - `sanitize_html_for_confluence()`: `file_download_links` 파라미터 추가
  - `normalize_filename()`: 퍼지 파일명 매칭 함수 추가
  - `confluence_update_page()`: `file_download_links` 파라미터 추가
  - XHTML `&amp;` 이스케이프 처리

**Dependencies**:
- `requirements.txt`: `requests` 라이브러리 추가

### 12.5 배포 및 업그레이드

**변경 사항**:
- `requests` 라이브러리 설치 필요: `pip install requests`
- 환경 변수: 변경 없음
- 기존 기능 호환성: 완전 유지

**업그레이드 방법**:
1. `pip install -r requirements.txt`
2. 서버 재시작
3. 브라우저 캐시 클리어 (Ctrl+F5)

---

## 13. v1.4.0 개선사항 (2026-04-09~10)

### 13.1 Codex Agent 기반 AI 챗봇 구현

#### 13.1.1 OpenAI Assistant API 연동

**목표**: 자연어로 Jira/Confluence 작업 및 문서 검색 수행

**구현 내용**:
- OpenAI Assistant API 기반 대화형 챗봇
- Tool calling 방식으로 Jira/Confluence API 호출
- 대화 세션 관리 및 이력 추적
- 실시간 스트리밍 응답

**핵심 파일**:
- `codex_agent.py`: CodexAgent 클래스, ToolExecutor
- `chat_service.py`: CodexChatService, 레거시 ChatService
- `codex_tools.json`: Tool 정의 (Jira/Confluence/RAG)

**지원 도구**:
1. `search_jira_issues`: 프로젝트 Key로 Jira 이슈 검색
2. `search_confluence_pages`: 프로젝트명으로 Confluence 페이지 검색
3. `fetch_confluence_page`: 페이지 ID/URL로 상세 조회
4. `search_documents`: RAG 기반 문서 검색
5. `list_documents`: 업로드된 문서 목록 조회

#### 13.1.2 Codex Agent Fallback 메커니즘

**문제**: OpenAI API 할당량 초과 시 챗봇 중단

**해결**: Rule-based fallback 구현

**Fallback 로직**:
```python
def _fallback_rule_based(self, user_message: str):
    # 1. 프로젝트 키 감지 (alphanumeric 지원)
    match_key = re.search(r"\b([A-Z][A-Z0-9]{1,9})\b", user_message)
    
    # 2. Confluence 페이지 ID 감지
    match_page_id = re.search(r"\[(\d{5,})\]", user_message)
    
    # 3. Confluence URL 감지
    match_url = re.search(r"(https?://\S*confluence\S*)", user_message)
    
    # 4. 키워드 기반 도구 선택
    if "jira" in msg_lower or "이슈" in msg_lower:
        return search_jira_issues(match_key)
    elif match_page_id or match_url:
        return fetch_confluence_page(page_ref)
```

**개선 사항**:
- 프로젝트 키 패턴: `J150`, `G80`, `F2` 등 alphanumeric 지원
- Confluence 페이지 ID: `[386584075]` 패턴 자동 감지
- URL 크롤링: Confluence URL 직접 입력 지원
- 키워드 확장: "프로젝트", "파일", "업로드", "첨부" 등

#### 13.1.3 Confluence 페이지 크롤링 강화

**하위 페이지 첨부 파일 검색**:
```python
# CQL 기반 전체 첨부 파일 검색
cql = f"type=attachment AND ancestor={page_id}"
# 최대 100개 첨부 파일 조회 (하위 페이지 포함)
```

**반환 정보**:
- 파일명, 크기, MIME 타입
- 소속 페이지 제목 및 ID
- 버전, 수정일, 수정자
- 최신순 정렬

**UI 표시**:
```
📎 첨부 파일 15개 (하위 페이지 포함):
  - 260309_KGM_J150_BSD_RQMT_R01_SOP.0 - rev 04.xlsx (v1, 2025-03-09, by 나현민) [RN2. KGM_SRR30_J150_NEW_G.H_PPSOP.0]
```

### 13.2 RAG (Retrieval Augmented Generation) 시스템

#### 13.2.1 문서 업로드 및 벡터 스토어 인덱싱

**목표**: 사양서, 법규, 메일 문서를 검색 가능하도록 색인화

**구현 파일**:
- `document_store.py`: DocumentStore 클래스
- `rag_service.py`: RAGService 클래스

**지원 문서 타입**:
- **사양서**: PDF, DOCX, TXT, MD, HTML
- **법규**: PDF, DOCX, TXT
- **메일**: MSG (Outlook), EML

**업로드 프로세스**:
```
1. 파일 업로드 (웹 UI)
   ↓
2. 메타데이터 추출
   - 제목, 버전, 부서, 시행일
   - 파일 해시 (중복 체크)
   ↓
3. OpenAI File API 업로드
   ↓
4. Vector Store에 색인화
   ↓
5. SQLite에 메타데이터 저장
```

**데이터베이스 스키마**:
```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    source_type TEXT,           -- spec, regulation, email
    title TEXT,
    version TEXT,
    effective_from TEXT,
    department TEXT,
    file_hash TEXT,             -- 중복 방지
    openai_file_id TEXT,
    vector_store_id TEXT,
    indexed_at TEXT
);

CREATE TABLE mail_metadata (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    sender TEXT,
    recipients TEXT,
    subject TEXT,
    sent_date TEXT,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);
```

#### 13.2.2 RAG 검색 및 출처 추적

**OpenAI Responses API 사용**:
```python
response = client.beta.threads.runs.create(
    thread_id=thread.id,
    assistant_id=assistant_id,
    tools=[{"type": "file_search"}],
    tool_resources={
        "file_search": {
            "vector_store_ids": [vector_store_id]
        }
    }
)
```

**Citation 강화**:
- 파일명, 제목, 버전
- 시행일, 부서
- 인용 텍스트 (quote)
- 메일 메타데이터 (발신자, 수신자, 제목)

**UI 표시**:
```
📚 출처:
  - 개인정보보호법 시행령 (v2023.03) [시행일: 2023-03-14] — "개인정보는 수집 후 3년간 보관..."
  - RE: 차량 사양 검토 요청 (발신: 김철수, 수신: 나현민, 2025-11-04)
```

### 13.3 Release Note 및 RQMT 섹션

#### 13.3.1 UI 구조 개편

**MCP Preview 제거**:
- 사이드바의 MCP 설정 JSON 표시 제거
- UI 간소화

**Release Note 개정 섹션**:
- 제목: "Release Note 개정"
- Quill 에디터 유지
- 파일 첨부 기능 포함

**Project Requirement 수정 섹션** (신규):
- 제목: "Project Requirement 수정"
- 일반 textarea (Quill 제거)
- 라벨: "Revision Note"
- 테이블 보기 모달 연동

#### 13.3.2 프로젝트 선택 시 자동 페이지 감지

**기능**: 프로젝트 선택 모달에서 프로젝트 선택 시 "2. Project Requirement - {프로젝트명}" 페이지 자동 감지

**구현**:
```javascript
// 페이지 로드 시 트리 노드 순회
treeNodes.forEach(node => {
  const txt = node.textContent.trim().replace(/\s*\[\d+\]\s*$/, '').trim();
  if (/^2\.\s*Project Requirement/i.test(txt)) {
    const pid = node.getAttribute('data-page-id');
    rqmtPageIdInput.value = pid;
    rqmtSelectedPageInput.value = `${txt} [${pid}]`;
  }
});
```

**사용자 경험**:
```
1. 프로젝트 선택 모달에서 "J150 [SRR-30]" 선택
   ↓
2. 페이지 리로드 후 트리 표시
   ↓
3. "2. Project Requirement - J150" 자동 감지
   ↓
4. RQMT 섹션의 "선택된 페이지"에 자동 입력
   ✅ "2. Project Requirement - J150 [386584075]"
```

#### 13.3.3 RQMT 테이블 모달 기능

**목표**: Confluence "2. Project Requirement" 페이지의 테이블을 모달로 표시하고 선택한 행을 textarea에 추가

**API 엔드포인트**:
```python
@frontend_bp.get("/api/fetch-rqmt-table/<page_id>")
def fetch_rqmt_table(page_id: str):
    # 1. Confluence REST API로 페이지 HTML 가져오기
    # 2. BeautifulSoup로 <table> 파싱
    # 3. 헤더와 행 데이터 JSON 반환
    return jsonify({
        "success": True,
        "headers": ["##", "Project Requirement", "Phase", "revision", "Date", "Author", "Comment"],
        "rows": [
            ["00", "291104 KGM J150 RED: RQMT_R01...", "PILOT", "00", "2025-11-4", "나현민", "initial"],
            ...
        ]
    })
```

**모달 UI**:
- 테이블 렌더링 (체크박스 포함)
- 전체 선택/해제 기능
- "선택 항목 추가" 버튼

**텍스트 변환 형식**:
```
[00] 291104 KGM J150 RED: RQMT_R01_PLot2Ta - rev 00.xlsx | PILOT | 00 | 2025-11-4 | 나현민 | initial
[01] 291107 KGM J150 RED: RQMT_R01_PLot2Ta - rev 01.xlsx | T | 01 | 2025-11-7 | 나현민 | [FVSE OTA] 미반영 기능 추가
```

**사용 플로우**:
```
1. "📋 테이블 보기" 버튼 클릭
   ↓
2. 모달에서 필요한 행 체크박스 선택
   ↓
3. "선택 항목 추가" 클릭
   ↓
4. textarea에 텍스트 형식으로 삽입
   ↓
5. 추가 내용 작성 후 "RQMT 등록" 제출
```

**기술적 개선**:
- BeautifulSoup `get_text(separator=" ", strip=True)`: 중첩 요소 텍스트 추출
- 퍼지 매칭: 한글 파일명 처리
- XHTML `&amp;` 이스케이프

### 13.4 챗봇 UI/UX 개선

#### 13.4.1 챗봇 패널 추가

**위치**: 메인 영역 하단

**기능**:
- 메시지 입력 및 전송
- 대화 이력 표시
- 모드 배지 표시 (Codex CLI, Codex Agent, Chat API, Rule Based)
- 대화 초기화 버튼
- 문서 업로드 버튼 (collapsible)

**모드 배지**:
```javascript
const modeMap = {
  'codex_cli': ['⚡ Codex CLI', '#10b981'],
  'codex_agent': ['🤖 Codex Agent', '#3b82f6'],
  'chat_api': ['💬 Chat API', '#8b5cf6'],
  'rule_based': ['📋 Rule Based', '#f59e0b'],
};
```

#### 13.4.2 문서 업로드 UI

**Collapsible 섹션**:
- 문서 타입 선택: 사양서, 법규, 메일
- 제목, 버전, 부서, 시행일 입력
- 파일 선택 (PDF, DOCX, MSG 등)
- 업로드 상태 표시

**업로드 결과**:
```
✅ 색인 완료: 개인정보보호법 시행령 (v2023.03)
✅ 중복: 차량 사양서 (v1.0) - 이미 등록됨
❌ 업로드 실패: 파일 형식 오류
```

### 13.5 변경된 파일 목록

**새 파일**:
- `codex_agent.py`: Codex Agent 및 ToolExecutor
- `codex_tools.json`: Tool 정의
- `document_store.py`: 문서 업로드 및 벡터 스토어
- `rag_service.py`: RAG 검색 및 Citation
- `chat_service.py`: CodexChatService, 레거시 ChatService

**수정 파일**:
- `backend.py`: 
  - AppConfig에 `openai_assistant_id`, `vector_store_*` 추가
  - `documents`, `mail_metadata` 테이블 추가
- `frontend.py`:
  - `/api/chat` 엔드포인트 추가
  - `/api/documents` (GET/POST) 추가
  - `/api/fetch-rqmt-table/<page_id>` 추가
- `templates/index.html`:
  - 챗봇 패널 추가
  - 문서 업로드 UI 추가
  - RQMT 테이블 모달 추가
  - MCP Preview 제거
- `static/styles.css`:
  - 챗봇 스타일 추가
  - 모드 배지 스타일 추가
- `requirements.txt`:
  - `beautifulsoup4`, `lxml`, `requests` 추가
- `.env.production.example`:
  - `OPENAI_ASSISTANT_ID`, `OPENAI_VECTOR_STORE_*` 추가

### 13.6 환경 변수 추가

```bash
# Codex Agent / RAG Configuration
OPENAI_ASSISTANT_ID=asst_xxxxxxxxxxxxxxxxxxxxx
OPENAI_VECTOR_STORE_SPEC=vs_xxxxxxxxxxxxxxxxxxxxx
OPENAI_VECTOR_STORE_REG=vs_xxxxxxxxxxxxxxxxxxxxx
OPENAI_VECTOR_STORE_EMAIL=vs_xxxxxxxxxxxxxxxxxxxxx
```

### 13.7 배포 및 업그레이드

**의존성 설치**:
```bash
pip install beautifulsoup4 lxml requests
```

**환경 변수 설정**:
1. OpenAI Assistant 생성
2. Vector Store 3개 생성 (사양서, 법규, 메일)
3. `.env`에 ID 입력

**업그레이드 방법**:
1. `pip install -r requirements.txt`
2. `.env` 업데이트
3. 서버 재시작
4. 브라우저 캐시 클리어

**호환성**:
- 기존 Jira/Confluence 기능: 완전 유지
- 기존 Release Note 기능: 완전 유지
- 신규 기능: 선택적 사용 (환경 변수 미설정 시 비활성화)

### 13.8 향후 개선 계획

**챗봇 기능**:
- [ ] 대화 이력 저장 및 불러오기
- [ ] 멀티턴 대화 컨텍스트 유지
- [ ] 사용자별 세션 관리

**RAG 기능**:
- [ ] 문서 재색인 기능
- [ ] 문서 삭제 기능
- [ ] 문서 검색 필터 (날짜, 부서, 버전)

**RQMT 기능**:
- [ ] 테이블 직접 편집
- [ ] 행 추가/삭제
- [ ] 버전 비교

---

## 14. v1.5.0 개선사항 (2026-04-10)

### 14.1 RQMT 테이블 파일 업로드 및 Confluence 첨부 파일 링크 개선

#### 14.1.1 파일 업로드 기능

**구현 내용**:
- RQMT 테이블의 "Project Requirement" 셀 클릭 시 파일 선택 다이얼로그 표시
- 파일 크기 제한: 최대 10MB
- 허용 확장자: `.xlsx`, `.xls`, `.pdf`, `.docx`, `.doc`
- 업로드 상태 표시 (주황색 "업로드 대기중" 텍스트)
- 행 추가 시 파일 자동 업로드 및 Confluence 첨부 파일 링크 생성

#### 14.1.2 Confluence 첨부 파일 링크 생성

**문제**: 파일 업로드 후 Confluence 테이블의 파일 링크 클릭 시 다운로드 안 됨

**원인 분석**:
1. Confluence Storage Format의 `<ac:link>` 매크로 구조 불완전
2. 파일명 불일치 (클라이언트 파일명 vs Confluence 정규화된 파일명)

**해결 방법**:
- 기존 테이블의 파일 링크 구조를 템플릿으로 사용하여 새 링크 생성
- Confluence API 응답의 `title` 필드에서 실제 파일명 추출
- 링크 구조 재생성 시 기존 링크의 속성 복사

**코드 구현** (`frontend.py`):
```python
# Find existing link template in table
existing_link_template = None
for row in table.find_all("tr")[1:]:
    cells = row.find_all("td")
    if len(cells) > 1:
        link = cells[1].find("ac:link")
        if link:
            existing_link_template = link
            break

# Recreate link structure based on template
if existing_link_template:
    link = soup.new_tag("ac:link")
    for attr, value in existing_link_template.attrs.items():
        link[attr] = value
    attachment = soup.new_tag("ri:attachment")
    attachment['ri:filename'] = str(actual_filename)
    link.append(attachment)
```

#### 14.1.3 중복 파일 덮어쓰기

**문제**: 같은 파일명으로 업로드 시 "Cannot add a new attachment with same file name" 오류 발생

**해결 방법** (`backend.py`):
- 기존 첨부 파일 목록에서 정규화된 파일명으로 비교
- 기존 파일 발견 시 업데이트 URL 사용 (`/child/attachment/{id}/data`)
- 새 파일인 경우 생성 URL 사용 (`/child/attachment`)

```python
# Normalized filename comparison
normalized_upload = file_storage.filename.replace(' ', '_').replace('-', '_')
normalized_existing = att_title.replace(' ', '_').replace('-', '_')
if normalized_upload == normalized_existing:
    existing_attachment_id = att.get('id')
```

#### 14.1.4 Windows cp949 인코딩 오류 해결

**문제**: Python `print()` 문에 유니코드 특수문자(⚠️, →)를 사용하면 Windows 터미널(cp949)에서 `UnicodeEncodeError` 발생, `except` 블록에서 프론트엔드로 전달됨

**해결**: 유니코드 특수문자를 ASCII 문자로 교체
- `⚠️` → `[WARNING]`
- `→` → `->`

### 14.2 셀 내 줄바꿈 개선

#### 14.2.1 Enter 키 동작 변경

**이전 동작**:
- `Enter`: 다음 셀로 이동
- `Alt+Enter`: 줄바꿈

**변경된 동작**:
- `Enter`: 셀 내 줄바꿈 (`document.execCommand('insertLineBreak')`)
- `Tab`: 다음 셀로 이동
- `Shift+Tab`: 이전 셀로 이동

**구현** (`templates/index.html`):
```javascript
// Enter: Insert line break within cell
if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey) {
  e.preventDefault();
  document.execCommand('insertLineBreak');
  cell.dispatchEvent(new Event('input', { bubbles: true }));
  return;
}

// Tab: Move to next cell
if (e.key === 'Tab' && !e.shiftKey) {
  e.preventDefault();
  // ... move to next cell
}
```

### 14.3 Project Requirement 페이지 자동 선택 개선

#### 14.3.1 페이지 매칭 조건 완화

**이전**: `^2\.\s*Project Requirement` (2번만 매칭)
**변경**: `Project Requirement` (번호에 관계없이 매칭)

- "2. Project Requirement - J150" ✅
- "3. Project Requirement - A200" ✅
- "Project Requirement - OV123" ✅

#### 14.3.2 RQMT 선택 페이지 고정

**변경**: Confluence 트리에서 다른 페이지를 클릭해도 "Project Requirement 수정" 섹션의 "선택된 페이지"가 변경되지 않도록 수정

- `autoFillRQMTSection()`에 의해서만 설정
- 트리 노드 클릭 핸들러에서 RQMT 필드 업데이트 코드 제거

### 14.4 프로젝트 코드 자동 입력

**구현**: 프로젝트 선택 시 트리 루트 노드의 title에서 프로젝트 코드를 추출하여 "프로젝트 코드" 필드에 자동 입력

**예시**: 트리 루트 "J150 [SRR-30]" → 프로젝트 코드 필드에 "J150" 자동 입력

```javascript
if (treeNodes.length > 0) {
  const rootTitle = treeNodes[0].textContent.trim().replace(/\s*\[\d+\]\s*$/, '').trim();
  const projectCode = rootTitle.split(/[\s\[]/)[0];
  document.getElementById('jira_project_search').value = projectCode;
}
```

### 14.5 변경된 파일

- `backend.py`: 첨부 파일 덮어쓰기 로직, 정규화 파일명 비교
- `frontend.py`: 링크 구조 템플릿 복사, 파일 업로드 개선, 인코딩 오류 수정
- `templates/index.html`: Enter/Tab 키 동작 변경, 프로젝트 코드 자동 입력, RQMT 페이지 고정, 매칭 조건 완화
- `static/styles.css`: 파일 업로드 셀 스타일

---

## 15. v1.6.0 개선사항 (2026-04-16)

### 15.1 변경 이력 요약

#### 15.1.1 Jira WBS 연동 강화

- `KGM_projectCode.csv`를 기준으로 프로젝트코드→WBS 코드 매핑 적용
- `비고` 컬럼이 `old`인 항목은 매핑/액션에서 제외
- 사이드바 버튼 텍스트를 `WBS 열기`로 변경
- 버튼 클릭 시 WBS Gantt 페이지를 직접 열도록 URL 고정

```text
https://jira.hlklemove.com/projects/{WBS_CODE}?selectedItem=jp.ricksoft.plugins.wbsgantt-for-jira:wbsgantt-project
```

#### 15.1.2 Jira 이슈 결과 표시 개선

- 결과 제목에 WBS 코드 표시: `Jira 이슈 검색 결과 (WBS: KGMJ150)`
- 카드 상단에 `이슈키 / 제목` 형태로 표시
- 완료 이슈 제외 기준을 문자열 매칭에서 Jira 실제 상태 카테고리로 변경
  - 제외 기준: `statusCategory.key == "done"`
- `JiraIssue` 데이터에 상태 카테고리 필드 추가
  - `status_category_key`
  - `status_category_name`

#### 15.1.3 챗봇 가독성/입력 UX 개선

- 응답 텍스트 줄바꿈 유지
- 번호형/불릿형 개조식 자동 렌더링
  - `1.`, `2)` → ordered list
  - `-`, `*`, `•` → unordered list
- 채팅창 이미지 붙여넣기(`Ctrl+V`) 지원
  - 썸네일 미리보기
  - 이미지별 제거 버튼
  - 전송 시 `/api/documents` 업로드 후 첨부 파일명 포함
- 이미지 첨부 질의 시 Confluence 트리 컨텍스트 자동 첨부
  - 제목 / 페이지ID / URL 목록
  - 스크린샷 질의에서 페이지 해석 정확도 향상

### 15.2 단계별 상세 사용자 가이드

#### 15.2.1 WBS 열기 사용 절차

1. 좌측 사이드바 `프로젝트 코드` 입력창에 코드 입력 (예: `J150`)
2. `WBS 열기` 버튼 클릭
3. 새 탭에서 아래 패턴의 URL이 열리는지 확인

```text
/projects/{WBS_CODE}?selectedItem=jp.ricksoft.plugins.wbsgantt-for-jira:wbsgantt-project
```

4. 기존 탭의 `Jira 이슈 검색 결과` 패널이 동시에 갱신되는지 확인

#### 15.2.2 Jira 이슈 결과 확인 절차

1. 결과 패널 제목에 WBS가 표시되는지 확인
   - 예: `Jira 이슈 검색 결과 (WBS: KGMJ150)`
2. 목록에서 카드 상단이 `이슈키 / 제목` 형태인지 확인
3. 상태 카테고리가 `Done`인 이슈가 제외되는지 확인
4. 진행중/검토중 등 완료 전 상태 이슈는 표시되는지 확인

#### 15.2.3 챗봇 이미지 질의 절차

1. 채팅 입력창 클릭 후 이미지 클립보드 붙여넣기(`Ctrl+V`)
2. 입력창 하단에 썸네일이 나타나는지 확인
3. 필요 시 `✕` 버튼으로 특정 이미지를 제거
4. 질의문을 입력하고 `전송` 클릭
5. 사용자 메시지에 첨부 파일 태그(`📎 파일명`)가 표시되는지 확인
6. 응답이 줄바꿈/개조식으로 읽기 좋게 표시되는지 확인
7. Confluence 페이지를 참조하는 질의에서 페이지 인식이 개선되었는지 확인

### 15.3 단계별 테스트 가이드

#### 시나리오 A: WBS URL 오픈 검증

1. 프로젝트 코드 `J150` 입력
2. `WBS 열기` 클릭
3. 기대 결과:
   - 새 탭 URL에 `selectedItem=jp.ricksoft.plugins.wbsgantt-for-jira:wbsgantt-project` 포함
   - 이슈 상세(`/issues/...`) 페이지가 아닌 WBS 화면으로 진입

#### 시나리오 B: Done 이슈 필터 검증

1. 동일 WBS로 이슈 목록 조회
2. Jira 원본 화면과 비교
3. 기대 결과:
   - `statusCategory=Done` 이슈는 결과 패널에서 미표시
   - 나머지 이슈는 정상 표시

#### 시나리오 C: 이미지 질의 검증

1. Confluence 트리가 표시된 상태에서 페이지 목록 화면 캡처
2. 챗봇 입력창에 붙여넣고 질의 전송
3. 기대 결과:
   - 이미지 업로드 및 첨부 태그 표시
   - 페이지를 찾지 못한다는 응답 빈도 감소
   - 페이지 ID/제목 기반 요약 정확도 향상

### 15.4 변경된 파일

- `backend.py`
  - WBS 매핑 소스 `KGM_projectCode.csv` 적용
  - `old` 항목 제외
  - Jira 이슈에 `statusCategory` 정보 포함
- `frontend.py`
  - WBS 매핑 기반 Jira 조회
  - `statusCategory.key == done` 필터 적용
- `templates/index.html`
  - `WBS 열기` 버튼 동작 및 URL 보정
  - Jira 결과 제목/카드 표시 개선
  - 챗봇 이미지 붙여넣기 + 컨텍스트 첨부 로직
- `static/styles.css`
  - 챗봇 개조식/줄바꿈 가독성 스타일
  - 이미지 미리보기/첨부 태그 스타일

---

## 16. v1.6.1 개선사항 (2026-04-17)

### 16.1 변경 이력 요약

#### 16.1.1 Codex Agent 이미지 비전 입력 적용

**문제**:
- 이미지를 붙여넣어도 챗봇이 `첨부된 이미지를 확인할 수 없음`으로 응답하는 케이스 발생

**원인**:
- 이미지 파일명이 텍스트로만 전달되고, 모델에 실제 이미지 바이트/URL이 전달되지 않음

**해결**:
- `/api/chat` 요청에 `image_attachments` 메타데이터(`doc_id`, `title`) 전달
- 서버에서 `documents` 테이블을 조회해 업로드 파일 경로를 안전 검증 후 `base64 data URL` 생성
- `CodexChatService` → `CodexAgent` 경로에 `vision_images` 인자 추가
- `CodexAgent`는 이미지가 포함된 요청에서 Chat API 멀티모달(`text + image_url`) 경로로 처리

#### 16.1.2 이미지 MIME 판정 보완

**문제**:
- `image.png`가 `application/octet-stream`으로 저장된 경우 비전 입력에서 제외됨

**해결**:
- MIME이 비어있거나 generic(`application/octet-stream`)일 때 확장자 기반 MIME 재판정 적용
  - `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.bmp`

### 16.2 안전성/제한 정책

- 이미지 비전 입력은 최대 3장까지 처리
- 장당 최대 5MB 제한
- 허용 MIME만 분석(`image/*` 제한 목록)
- `Data/documents` 하위 파일만 허용(경로 탈출 방지)
- 일부 이미지 실패 시 나머지 이미지는 계속 분석하고 경고 메시지 표시

### 16.3 검증 결과

- Python 문법 검사 통과:

```bash
py -3 -m py_compile frontend.py chat_service.py codex_agent.py
```

- UI 동작 확인:
  - 이미지 붙여넣기/첨부 태그 표시 유지
  - 백엔드 제외 사유가 있을 경우 `참고:` 시스템 메시지로 노출

### 16.4 변경된 파일

- `templates/index.html`
  - 이미지 업로드 결과의 `doc_id`를 채팅 payload에 포함
  - 서버 warning 표시 로직 추가
- `frontend.py`
  - `image_attachments` 수신 및 문서 조회/base64 변환
  - 이미지 제한(개수/용량/MIME/경로) 검증
  - MIME 재판정(확장자 fallback) 보완
- `chat_service.py`
  - `CodexChatService.process_message(..., vision_images=...)` 확장
- `codex_agent.py`
  - 멀티모달 user message(`text + image_url`) 지원
  - 이미지 포함 요청 시 Chat API 경로 우선 처리

---

**문서 버전**: v1.6.1  
**최종 수정일**: 2026-04-17  
**작성자**: backas-D  
**문서 상태**: 실제 구현 기반 완료
