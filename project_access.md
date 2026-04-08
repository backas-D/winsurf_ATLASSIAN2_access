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

**문서 버전**: v1.2.0  
**최종 수정일**: 2026-04-08  
**작성자**: backas-D  
**문서 상태**: 실제 구현 기반 완료
