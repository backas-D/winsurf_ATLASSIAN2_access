# ATLASSIAN2 Access - Distribution Package Creator
# This script creates a ZIP package for distribution to end users

param(
    [Parameter(Mandatory=$false)]
    [string]$OutputDir = ".\dist",
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ATLASSIAN2 Access - Package Creator" -ForegroundColor Cyan
Write-Host " Version: $Version" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ProjectRoot = $PSScriptRoot
$PackageName = "ATLASSIAN2_Access_v$Version"
$TempDir = Join-Path $env:TEMP $PackageName
$OutputPath = Join-Path $OutputDir "$PackageName.zip"

# Create output directory
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Clean temp directory
if (Test-Path $TempDir) {
    Remove-Item -Path $TempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $TempDir | Out-Null

Write-Host "[INFO] Creating distribution package..." -ForegroundColor Green
Write-Host "  Source: $ProjectRoot" -ForegroundColor White
Write-Host "  Temp: $TempDir" -ForegroundColor White
Write-Host "  Output: $OutputPath" -ForegroundColor White
Write-Host ""

# Files and directories to include
$FilesToCopy = @(
    # Core Python files
    "main.py",
    "backend.py",
    "frontend.py",
    "chat_service.py",
    "codex_agent.py",
    "codex_tools.json",
    "document_store.py",
    "rag_service.py",
    
    # Configuration and scripts
    "requirements.txt",
    "Run_production.bat",
    "Run_app.bat",
    "setup_firewall.ps1",
    ".env.production.example",
    ".gitignore",
    
    # Documentation
    "README.md",
    "QUICKSTART.md",
    "DEPLOYMENT.md",
    "ENV_SETUP_GUIDE.md",
    "DISTRIBUTION_GUIDE.md",
    "project_access.md"
)

$DirectoriesToCopy = @(
    "static",
    "templates",
    "Data"
)

# Copy files
Write-Host "[INFO] Copying files..." -ForegroundColor Green
foreach ($file in $FilesToCopy) {
    $sourcePath = Join-Path $ProjectRoot $file
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $TempDir -Force
        Write-Host "  ✓ $file" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ $file (not found, skipping)" -ForegroundColor Yellow
    }
}

# Copy directories
Write-Host "[INFO] Copying directories..." -ForegroundColor Green
foreach ($dir in $DirectoriesToCopy) {
    $sourcePath = Join-Path $ProjectRoot $dir
    if (Test-Path $sourcePath) {
        Copy-Item -Path $sourcePath -Destination $TempDir -Recurse -Force
        Write-Host "  ✓ $dir\" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ $dir\ (not found, skipping)" -ForegroundColor Yellow
    }
}

# Create installation guide
Write-Host "[INFO] Creating installation guide..." -ForegroundColor Green

$InstallGuide = @"
# ATLASSIAN2 Access - 설치 가이드

버전: $Version
배포일: $(Get-Date -Format "yyyy-MM-dd")

## 빠른 설치 (5분)

### 1. 필수 요구사항

- **Python 3.12 이상** (Python 3.13 권장)
- **Windows 10/11** 또는 **Windows Server 2016 이상**

### 2. 설치 단계

#### 2-1. 압축 해제

이 ZIP 파일을 원하는 위치에 압축 해제합니다.
예: ``C:\Tools\ATLASSIAN2_Access``

#### 2-2. 환경 설정

1. ``.env.production.example`` 파일을 ``.env``로 복사
2. ``.env`` 파일을 열어서 다음 항목 수정:

``````bash
# SECRET_KEY 생성 (PowerShell에서 실행)
python -c "import secrets; print(secrets.token_hex(32))"

# .env 파일에 설정
FLASK_ENV=production
SECRET_KEY=<위에서 생성한 키>

# Atlassian API 정보 (필수)
JIRA_BASE_URL=https://your-company.atlassian.net
JIRA_PAT=<your-jira-personal-access-token>
CONFLUENCE_BASE_URL=https://your-company.atlassian.net
CONFLUENCE_PAT=<your-confluence-personal-access-token>

# OpenAI API (선택사항)
OPENAI_API_KEY=<your-openai-api-key>
OPENAI_MODEL=gpt-4
``````

**PAT 생성 방법:**
- **Jira:** Profile → Personal Access Tokens → Create Token
- **Confluence:** 환경설정 → 개인용 액세스 토큰 → 토큰 만들기

#### 2-3. 방화벽 설정 (외부 접근 시)

PowerShell을 **관리자 권한으로** 실행:

``````powershell
cd "C:\Tools\ATLASSIAN2_Access"
PowerShell -ExecutionPolicy Bypass -File .\setup_firewall.ps1
``````

#### 2-4. 애플리케이션 실행

``````batch
Run_production.bat
``````

자동으로 브라우저가 열리며 http://127.0.0.1:5000 으로 접속됩니다.

## 접속 URL

- **로컬:** http://127.0.0.1:5000
- **내부 네트워크:** http://[서버-IP]:5000
- **외부 인터넷:** http://[공인-IP]:5000 (포트 포워딩 필요)

## 문제 해결

### Python이 없는 경우

Python 다운로드: https://www.python.org/downloads/

설치 시 **"Add Python to PATH"** 옵션 체크!

### 서버가 시작되지 않는 경우

1. Python 버전 확인: ``python --version`` (3.12 이상)
2. ``.env`` 파일 존재 확인
3. ``logs\error.log`` 파일 확인

### API 연결 실패 (404 에러)

1. ``.env`` 파일의 URL이 정확한지 확인
2. PAT 토큰이 유효한지 확인
3. 네트워크 연결 확인

## 상세 문서

- **빠른 시작:** ``QUICKSTART.md``
- **전체 배포 가이드:** ``DEPLOYMENT.md``
- **환경 설정 가이드:** ``ENV_SETUP_GUIDE.md``
- **프로젝트 문서:** ``README.md``

## 보안 주의사항

⚠️ **중요:**
- ``.env`` 파일에는 민감한 정보(API 키, PAT)가 포함됩니다
- ``.env`` 파일을 절대 외부에 공유하지 마세요
- 각 사용자는 자신의 PAT를 사용해야 합니다
- 정기적으로 PAT를 갱신하세요

## 지원

문제가 발생하면:
1. ``logs\error.log`` 파일 확인
2. 문서 참조 (``DEPLOYMENT.md``, ``ENV_SETUP_GUIDE.md``)
3. IT 지원팀 문의

---

**설치 완료 후 서버를 실행하면 바로 사용 가능합니다!**
"@

Set-Content -Path (Join-Path $TempDir "INSTALL.md") -Value $InstallGuide -Encoding UTF8
Write-Host "  ✓ INSTALL.md" -ForegroundColor Gray

# Create README for distribution
$DistReadme = @"
# ATLASSIAN2 Access v$Version

Atlassian 제품군(Jira, Confluence)과 연동하여 프로젝트 관리를 지원하는 웹 애플리케이션입니다.

## 주요 기능

- ✅ Confluence 페이지 검색 및 트리 구조 표시
- ✅ Jira 이슈 검색 및 관리
- ✅ Confluence 페이지 수정 및 파일 업로드
- ✅ Jira 이슈 생성 및 수정
- ✅ 웹 기반 사용자 인터페이스

## 빠른 시작

1. **압축 해제:** 원하는 위치에 압축 해제
2. **환경 설정:** ``.env.production.example``을 ``.env``로 복사 후 수정
3. **실행:** ``Run_production.bat`` 더블클릭

자세한 설치 방법은 ``INSTALL.md`` 파일을 참조하세요.

## 시스템 요구사항

- Windows 10/11 또는 Windows Server 2016 이상
- Python 3.12 이상
- 인터넷 연결 (Atlassian API 호출용)

## 문서

- ``INSTALL.md`` - 설치 가이드 (필독!)
- ``QUICKSTART.md`` - 빠른 시작 가이드
- ``DEPLOYMENT.md`` - 상세 배포 가이드
- ``ENV_SETUP_GUIDE.md`` - 환경 설정 가이드

## 라이선스 및 보안

⚠️ 이 소프트웨어는 내부 사용 목적으로 배포됩니다.
⚠️ ``.env`` 파일에 포함된 API 키와 토큰은 절대 외부에 공유하지 마세요.

---

배포 버전: $Version
배포일: $(Get-Date -Format "yyyy-MM-dd")
"@

Set-Content -Path (Join-Path $TempDir "README_DIST.md") -Value $DistReadme -Encoding UTF8
Write-Host "  ✓ README_DIST.md" -ForegroundColor Gray

# Create version info file
$VersionInfo = @{
    version = $Version
    build_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    python_required = "3.12+"
    platform = "Windows"
}
$VersionInfo | ConvertTo-Json | Set-Content -Path (Join-Path $TempDir "version.json") -Encoding UTF8
Write-Host "  ✓ version.json" -ForegroundColor Gray

# Create ZIP package
Write-Host ""
Write-Host "[INFO] Creating ZIP package..." -ForegroundColor Green

if (Test-Path $OutputPath) {
    Remove-Item -Path $OutputPath -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($TempDir, $OutputPath)

# Clean up temp directory
Remove-Item -Path $TempDir -Recurse -Force

# Get file size
$FileSize = (Get-Item $OutputPath).Length
$FileSizeMB = [math]::Round($FileSize / 1MB, 2)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Package Created Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Package: $OutputPath" -ForegroundColor White
Write-Host "  Size: $FileSizeMB MB" -ForegroundColor White
Write-Host ""
Write-Host "배포 패키지가 생성되었습니다!" -ForegroundColor Green
Write-Host "이 ZIP 파일을 사용자들에게 배포하세요." -ForegroundColor White
Write-Host ""
Write-Host "User Installation Steps:" -ForegroundColor Cyan
Write-Host "  1. Extract ZIP file" -ForegroundColor White
Write-Host "  2. Read INSTALL.md" -ForegroundColor White
Write-Host "  3. Configure .env file" -ForegroundColor White
Write-Host "  4. Run Run_production.bat" -ForegroundColor White
Write-Host ""
