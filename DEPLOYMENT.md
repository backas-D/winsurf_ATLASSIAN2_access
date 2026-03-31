# ATLASSIAN2 Access - 배포 가이드

이 문서는 ATLASSIAN2 Access 애플리케이션을 Windows 서버에서 프로덕션 환경으로 배포하는 방법을 설명합니다.

## 목차
1. [사전 요구사항](#사전-요구사항)
2. [배포 준비](#배포-준비)
3. [프로덕션 배포](#프로덕션-배포)
4. [보안 설정](#보안-설정)
5. [네트워크 설정](#네트워크-설정)
6. [모니터링 및 로깅](#모니터링-및-로깅)
7. [트러블슈팅](#트러블슈팅)
8. [백업 및 복구](#백업-및-복구)

---

## 사전 요구사항

### 필수 소프트웨어
- **Python 3.12 이상** (Python 3.13 권장)
- **Windows 10/11 또는 Windows Server 2016 이상**
- **관리자 권한** (방화벽 설정 및 포트 개방용)

### 네트워크 요구사항
- **고정 IP 주소** (내부 네트워크)
- **공인 IP 주소** (외부 인터넷 접근 시)
- **포트 5000** 개방 가능
- **안정적인 인터넷 연결** (Atlassian API 호출용)

---

## 배포 준비

### 1. 의존성 설치

프로젝트 루트 디렉터리에서 다음 명령을 실행합니다:

```batch
Run_production.bat
```

이 스크립트는 자동으로:
- Python 가상환경 생성 (`.venv`)
- 필요한 패키지 설치 (`requirements.txt`)
- 프로덕션 서버 시작

### 2. 환경 변수 설정

#### SECRET_KEY 생성

보안을 위해 강력한 SECRET_KEY를 생성해야 합니다:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

#### .env 파일 구성

`.env.production.example` 파일을 `.env`로 복사하고 실제 값으로 수정합니다:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<위에서 생성한 SECRET_KEY>

# OpenAI Configuration
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=gpt-4

# Jira Configuration
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_PAT=<your-jira-personal-access-token>

# Confluence Configuration
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_PAT=<your-confluence-personal-access-token>
```

**⚠️ 중요:** `.env` 파일은 절대 Git에 커밋하지 마세요!

---

## 프로덕션 배포

### 방법 1: 배치 파일 실행 (권장)

```batch
Run_production.bat
```

이 방법은:
- ✅ 자동으로 의존성 설치
- ✅ 프로덕션 모드로 실행 (Waitress WSGI 서버)
- ✅ 외부 접근 허용 (`0.0.0.0:5000`)
- ✅ 로그 파일 자동 생성
- ✅ 멀티스레드 지원 (4 threads)

### 방법 2: 수동 실행

```powershell
# 가상환경 활성화
.venv\Scripts\activate

# 프로덕션 서버 실행
python -m waitress --host=0.0.0.0 --port=5000 --threads=4 main:app
```

### 서버 접근 URL

배포 후 다음 URL로 접근 가능합니다:

- **로컬:** `http://127.0.0.1:5000`
- **내부 네트워크:** `http://<서버-IP>:5000`
- **외부 인터넷:** `http://<공인-IP>:5000`

---

## 보안 설정

### 1. HTTPS 설정 (강력 권장)

프로덕션 환경에서는 반드시 HTTPS를 사용해야 합니다.

#### 옵션 A: 자체 서명 인증서 (테스트용)

```powershell
# OpenSSL 설치 필요
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
```

#### 옵션 B: Let's Encrypt (권장)

Windows에서 Let's Encrypt 사용:
1. **Certbot for Windows** 설치
2. 인증서 발급 및 자동 갱신 설정
3. 리버스 프록시 (nginx, IIS) 구성

#### 옵션 C: 리버스 프록시 사용

**nginx 설정 예시:**

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2. 방화벽 설정

#### Windows Defender 방화벽 규칙 추가

관리자 권한으로 PowerShell 실행:

```powershell
# 포트 5000 인바운드 규칙 추가
New-NetFirewallRule -DisplayName "ATLASSIAN2 Access - Port 5000" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5000 `
    -Action Allow `
    -Profile Domain,Private,Public

# 특정 IP 범위만 허용 (선택사항)
New-NetFirewallRule -DisplayName "ATLASSIAN2 Access - Restricted" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 5000 `
    -RemoteAddress 192.168.1.0/24 `
    -Action Allow
```

#### 방화벽 규칙 확인

```powershell
Get-NetFirewallRule -DisplayName "ATLASSIAN2 Access*"
```

#### 방화벽 규칙 삭제 (필요시)

```powershell
Remove-NetFirewallRule -DisplayName "ATLASSIAN2 Access - Port 5000"
```

### 3. 파일 권한 설정

`.env` 파일의 권한을 제한합니다:

```powershell
# 관리자와 현재 사용자만 읽기 가능하도록 설정
icacls .env /inheritance:r
icacls .env /grant:r "%USERNAME%:(R)"
icacls .env /grant:r "Administrators:(F)"
```

---

## 네트워크 설정

### 1. 내부 네트워크 접근

서버의 내부 IP 주소 확인:

```powershell
ipconfig
```

`IPv4 주소`를 확인하고 `http://<내부-IP>:5000`으로 접근합니다.

### 2. 외부 인터넷 접근

#### 공인 IP 확인

```powershell
# PowerShell에서 공인 IP 확인
(Invoke-WebRequest -Uri "https://api.ipify.org").Content
```

#### 포트 포워딩 설정

라우터 관리 페이지에서:
1. **포트 포워딩** 메뉴 접속
2. **외부 포트:** 5000 → **내부 포트:** 5000
3. **내부 IP:** 서버의 내부 IP 주소
4. **프로토콜:** TCP

#### 동적 DNS (선택사항)

공인 IP가 자주 변경되는 경우:
- **No-IP**, **DuckDNS**, **Dynu** 등의 무료 DDNS 서비스 사용
- 도메인 이름으로 접근 가능 (예: `myapp.ddns.net`)

---

## 모니터링 및 로깅

### 로그 파일 위치

프로덕션 모드에서는 다음 위치에 로그가 저장됩니다:

```
logs/
├── app.log              # 일반 애플리케이션 로그
├── error.log            # 에러 로그
└── production_*.log     # 프로덕션 서버 실행 로그
```

### 로그 확인

```powershell
# 최근 로그 확인
Get-Content logs\app.log -Tail 50

# 에러 로그 확인
Get-Content logs\error.log -Tail 50

# 실시간 로그 모니터링
Get-Content logs\app.log -Wait
```

### 로그 로테이션

로그 파일은 자동으로 로테이션됩니다:
- **최대 파일 크기:** 10MB
- **백업 파일 수:** 10개
- **자동 압축:** 지원

### 성능 모니터링

Windows 작업 관리자 또는 PowerShell로 모니터링:

```powershell
# Python 프로세스 확인
Get-Process python

# 메모리 사용량 확인
Get-Process python | Select-Object Name, CPU, WorkingSet
```

---

## 트러블슈팅

### 문제 1: 서버가 시작되지 않음

**증상:** `Run_production.bat` 실행 시 오류 발생

**해결 방법:**
1. Python 버전 확인: `python --version` (3.12 이상)
2. `.env` 파일 존재 확인
3. 가상환경 재생성: `.venv` 폴더 삭제 후 재실행
4. 로그 파일 확인: `logs\error.log`

### 문제 2: 외부에서 접근 불가

**증상:** 내부에서는 접근되지만 외부에서 접근 안 됨

**해결 방법:**
1. 방화벽 규칙 확인
2. 라우터 포트 포워딩 설정 확인
3. 공인 IP 확인 및 변경 여부 체크
4. ISP의 포트 차단 여부 확인 (일부 ISP는 특정 포트 차단)

### 문제 3: Atlassian API 연결 실패

**증상:** Confluence/Jira 검색 시 오류 발생

**해결 방법:**
1. `.env` 파일의 API 키 확인
2. Atlassian PAT 유효성 확인
3. 네트워크 연결 확인
4. Atlassian 서비스 상태 확인

### 문제 4: 포트 5000 이미 사용 중

**증상:** "Address already in use" 오류

**해결 방법:**
```powershell
# 포트 5000을 사용하는 프로세스 확인
netstat -ano | findstr :5000

# 프로세스 종료 (PID 확인 후)
taskkill /PID <PID> /F
```

### 문제 5: 파일 업로드 실패

**증상:** 25MB 이상 파일 업로드 시 오류

**해결 방법:**
- `main.py`의 `MAX_CONTENT_LENGTH` 설정 변경
- 현재 제한: 25MB

---

## 백업 및 복구

### 백업 대상

정기적으로 다음 항목을 백업해야 합니다:

```
ATLASSIAN2_access/
├── .env                    # 환경 설정 (중요!)
├── project_data.db         # SQLite 데이터베이스
├── Data/                   # 업로드된 파일
└── logs/                   # 로그 파일 (선택사항)
```

### 백업 스크립트 예시

```powershell
# backup.ps1
$BackupDir = "D:\Backups\ATLASSIAN2_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $BackupDir

Copy-Item .env $BackupDir
Copy-Item project_data.db $BackupDir
Copy-Item -Recurse Data $BackupDir
Copy-Item -Recurse logs $BackupDir

Write-Host "Backup completed: $BackupDir"
```

### 복구 절차

1. 서버 중지
2. 백업 파일 복원
3. `.env` 파일 권한 재설정
4. 서버 재시작
5. 정상 작동 확인

---

## 보안 체크리스트

배포 전 다음 항목을 확인하세요:

- [ ] `.env` 파일에 강력한 SECRET_KEY 설정
- [ ] `.env` 파일 권한 제한 (읽기 전용)
- [ ] `.env` 파일이 `.gitignore`에 포함되어 있음
- [ ] HTTPS 설정 (프로덕션 환경)
- [ ] 방화벽 규칙 설정
- [ ] 불필요한 포트 차단
- [ ] 정기적인 백업 계획 수립
- [ ] 로그 모니터링 체계 구축
- [ ] Atlassian PAT 정기 갱신 계획
- [ ] 애플리케이션 업데이트 계획

---

## 추가 리소스

- [Flask 공식 문서](https://flask.palletsprojects.com/)
- [Waitress 문서](https://docs.pylonsproject.org/projects/waitress/)
- [Atlassian REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [Let's Encrypt](https://letsencrypt.org/)

---

## 지원 및 문의

문제가 발생하거나 질문이 있으시면:
1. `logs/error.log` 파일 확인
2. 프로젝트 문서 참조 (`README.md`, `project_access.md`)
3. 내부 지원팀 문의

---

**마지막 업데이트:** 2026-03-31
