# 빠른 시작 가이드 - 프로덕션 배포

이 가이드는 ATLASSIAN2 Access 애플리케이션을 프로덕션 환경에 빠르게 배포하는 방법을 설명합니다.

## 1단계: 환경 설정 (5분)

### SECRET_KEY 생성

PowerShell에서 실행:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

생성된 키를 복사해 두세요.

### .env 파일 설정

1. `.env.production.example` 파일을 `.env`로 복사
2. 다음 항목을 실제 값으로 수정:

```bash
FLASK_ENV=production
SECRET_KEY=<위에서 생성한 키>
OPENAI_API_KEY=<your-key>
JIRA_BASE_URL=<your-jira-url>
JIRA_PAT=<your-jira-token>
CONFLUENCE_BASE_URL=<your-confluence-url>
CONFLUENCE_PAT=<your-confluence-token>
```

## 2단계: 방화벽 설정 (2분)

**관리자 권한으로** PowerShell 실행:

```powershell
# 포트 5000 개방
.\setup_firewall.ps1

# 특정 IP 범위만 허용하려면:
# .\setup_firewall.ps1 -RemoteAddress "192.168.1.0/24"
```

## 3단계: 프로덕션 서버 실행 (1분)

```batch
Run_production.bat
```

## 4단계: 접속 확인

브라우저에서 다음 URL로 접속:

- **로컬:** http://127.0.0.1:5000
- **네트워크:** http://[서버-IP]:5000
- **외부:** http://[공인-IP]:5000

## 완료! 🎉

애플리케이션이 프로덕션 모드로 실행 중입니다.

### 로그 확인

```powershell
# 애플리케이션 로그
Get-Content logs\app.log -Tail 50

# 에러 로그
Get-Content logs\error.log -Tail 50
```

### 서버 중지

`Ctrl+C`를 눌러 서버를 중지합니다.

---

## 추가 설정 (선택사항)

### HTTPS 설정

프로덕션 환경에서는 HTTPS 사용을 강력히 권장합니다.
자세한 내용은 `DEPLOYMENT.md`의 "보안 설정" 섹션을 참조하세요.

### 자동 시작 설정

Windows 작업 스케줄러를 사용하여 시스템 부팅 시 자동 시작:

1. 작업 스케줄러 실행
2. "기본 작업 만들기" 선택
3. 트리거: "컴퓨터를 시작할 때"
4. 작업: `Run_production.bat` 경로 지정

---

## 문제 해결

### 서버가 시작되지 않음
- Python 버전 확인: `python --version` (3.12 이상 필요)
- `.env` 파일 존재 확인
- `logs\error.log` 확인

### 외부에서 접속 안 됨
- 방화벽 규칙 확인: `Get-NetFirewallRule -DisplayName "ATLASSIAN2*"`
- 라우터 포트 포워딩 설정 확인 (외부 접속 시)
- 공인 IP 확인

### 자세한 문서
전체 배포 가이드는 `DEPLOYMENT.md`를 참조하세요.
