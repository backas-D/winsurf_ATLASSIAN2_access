# 배포 가이드 - 여러 사용자에게 전달하기

이 문서는 ATLASSIAN2 Access 애플리케이션을 여러 사용자에게 배포하는 방법을 설명합니다.

## 배포 패키지 생성

### 자동 패키징 (권장)

PowerShell에서 다음 명령 실행:

```powershell
.\create_distribution_package.ps1
```

또는 버전 지정:

```powershell
.\create_distribution_package.ps1 -Version "1.0.0"
```

생성된 패키지: `dist\ATLASSIAN2_Access_v1.0.0.zip`

### 수동 패키징

다음 파일과 폴더를 ZIP으로 압축:

#### 필수 파일

```
ATLASSIAN2_Access/
├── main.py                      # 메인 애플리케이션
├── backend.py                   # 백엔드 로직
├── frontend.py                  # 프론트엔드 라우팅
├── requirements.txt             # Python 의존성
├── Run_production.bat           # 프로덕션 실행 스크립트
├── Run_app.bat                  # 개발 모드 실행 스크립트
├── setup_firewall.ps1           # 방화벽 설정 스크립트
├── .env.production.example      # 환경 변수 템플릿
├── .gitignore                   # Git 제외 파일 목록
├── README.md                    # 프로젝트 문서
├── QUICKSTART.md                # 빠른 시작 가이드
├── DEPLOYMENT.md                # 상세 배포 가이드
├── ENV_SETUP_GUIDE.md           # 환경 설정 가이드
├── project_access.md            # 프로젝트 개요
├── static/                      # 정적 파일 (CSS, JS, 이미지)
├── templates/                   # HTML 템플릿
└── Data/                        # 데이터 저장 폴더 (빈 폴더)
```

#### 제외할 파일/폴더

**⚠️ 절대 포함하지 말 것:**

```
.env                    # 실제 환경 변수 (API 키 포함!)
.venv/                  # 가상환경
__pycache__/            # Python 캐시
logs/                   # 로그 파일
.tmp/                   # 임시 파일
project_data.db         # 데이터베이스 (개인 데이터 포함)
*.pyc                   # 컴파일된 Python 파일
```

## 사용자에게 전달할 내용

### 1. ZIP 파일

생성된 배포 패키지 ZIP 파일

### 2. 설치 안내 문서

사용자에게 다음 내용을 안내:

```
ATLASSIAN2 Access 설치 방법

1. 필수 요구사항
   - Python 3.12 이상 설치
   - Windows 10/11 또는 Windows Server

2. 설치 단계
   ① ZIP 파일을 원하는 위치에 압축 해제
      예: C:\Tools\ATLASSIAN2_Access
   
   ② .env.production.example 파일을 .env로 복사
   
   ③ .env 파일 수정:
      - SECRET_KEY 생성 및 입력
      - Jira/Confluence URL 및 PAT 입력
   
   ④ Run_production.bat 실행

3. 접속
   - 브라우저 자동 실행
   - 또는 http://127.0.0.1:5000 접속

자세한 내용은 ZIP 파일 내 INSTALL.md 참조
```

### 3. API 키 발급 안내

각 사용자는 **자신의 PAT**를 발급받아야 합니다:

**Jira PAT 발급:**
1. Jira 로그인
2. Profile → Personal Access Tokens
3. Create Token
4. 토큰 복사 후 .env에 입력

**Confluence PAT 발급:**
1. Confluence 로그인
2. 환경설정 → 개인용 액세스 토큰
3. 토큰 만들기
4. 토큰 복사 후 .env에 입력

## 배포 체크리스트

배포 전 확인사항:

- [ ] `.env` 파일이 패키지에 포함되지 않았는지 확인
- [ ] `project_data.db` 파일이 포함되지 않았는지 확인
- [ ] `.venv` 폴더가 포함되지 않았는지 확인
- [ ] `logs` 폴더가 포함되지 않았는지 확인
- [ ] `INSTALL.md` 또는 설치 가이드 포함 확인
- [ ] `requirements.txt`에 모든 의존성 포함 확인
- [ ] `Run_production.bat` 스크립트 동작 테스트
- [ ] 문서 파일들이 최신 상태인지 확인

## 사용자별 설정

각 사용자는 다음을 개별적으로 설정해야 합니다:

### 필수 설정

1. **SECRET_KEY** - 각자 생성
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Atlassian PAT** - 각자 발급
   - JIRA_PAT
   - CONFLUENCE_PAT

3. **Atlassian URL** - 회사 공통 또는 개별
   - JIRA_BASE_URL
   - CONFLUENCE_BASE_URL

### 선택 설정

- **OPENAI_API_KEY** - OpenAI 기능 사용 시
- **방화벽 설정** - 외부 접근 허용 시

## 중앙 관리 vs 개별 관리

### 옵션 1: 중앙 관리 (권장하지 않음)

- 서버 1대에 설치
- 모든 사용자가 네트워크로 접속
- 장점: 관리 편의성
- 단점: 보안 위험, 단일 장애점

### 옵션 2: 개별 설치 (권장)

- 각 사용자 PC에 개별 설치
- 각자의 PAT 사용
- 장점: 보안, 독립성
- 단점: 개별 설치 필요

## 버전 관리

### 버전 번호 규칙

`v{major}.{minor}.{patch}`

예: v1.0.0, v1.1.0, v2.0.0

### 업데이트 배포

1. 변경사항 문서화
2. 버전 번호 업데이트
3. 새 배포 패키지 생성
4. 사용자에게 업데이트 안내

## 보안 주의사항

### 배포 시 주의사항

⚠️ **절대 포함하지 말 것:**
- 실제 `.env` 파일
- API 키, PAT 토큰
- 데이터베이스 파일
- 로그 파일
- 개인 데이터

⚠️ **사용자 교육:**
- `.env` 파일 보안 중요성
- PAT 공유 금지
- 정기적인 PAT 갱신
- 파일 권한 설정

## 문제 해결 지원

### 일반적인 문제

1. **Python 미설치**
   - Python 다운로드 링크 제공
   - 설치 가이드 제공

2. **의존성 설치 실패**
   - 인터넷 연결 확인
   - pip 업그레이드 안내

3. **API 연결 실패**
   - URL 확인
   - PAT 유효성 확인
   - 네트워크 확인

4. **방화벽 문제**
   - 관리자 권한 필요 안내
   - 수동 설정 방법 제공

## 배포 패키지 테스트

배포 전 테스트 절차:

1. **깨끗한 환경에서 테스트**
   ```powershell
   # 새 폴더에 압축 해제
   # Python 가상환경 없는 상태에서 테스트
   ```

2. **.env 설정 테스트**
   - 템플릿에서 .env 생성
   - 실제 값 입력
   - 서버 시작 확인

3. **기능 테스트**
   - Confluence 검색
   - Jira 검색
   - 페이지 수정
   - 파일 업로드

4. **문서 확인**
   - 모든 링크 동작 확인
   - 설명이 명확한지 확인

## 자동화 스크립트 사용

배포 패키지 자동 생성:

```powershell
# 기본 버전 (1.0.0)
.\create_distribution_package.ps1

# 특정 버전
.\create_distribution_package.ps1 -Version "1.2.0"

# 출력 디렉터리 지정
.\create_distribution_package.ps1 -Version "1.0.0" -OutputDir "D:\Releases"
```

생성된 파일:
- `dist\ATLASSIAN2_Access_v{version}.zip`

## 라이선스 및 사용 조건

배포 시 명시할 내용:

- 내부 사용 목적
- 재배포 금지
- 보안 준수 사항
- 지원 연락처

---

**배포 준비가 완료되었습니다!**

`create_distribution_package.ps1` 스크립트를 실행하여
배포 패키지를 생성하세요.
