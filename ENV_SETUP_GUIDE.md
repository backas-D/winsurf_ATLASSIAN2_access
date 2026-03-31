# .env 파일 설정 가이드

현재 애플리케이션이 실행되었지만 Confluence/Jira API 연결이 실패하고 있습니다.
`.env` 파일에 실제 API 정보를 입력해야 합니다.

## 현재 문제

스크린샷의 에러:
```
GET https://your-confluence-instance.atlassian.net/rest/api/content/search?...
failed with 404. {"errorMessage": "Site temporarily unavailable"}
```

이는 `.env` 파일에 기본 템플릿 값이 그대로 있어서 발생하는 문제입니다.

## 해결 방법

### 1단계: .env 파일 열기

프로젝트 루트의 `.env` 파일을 텍스트 에디터로 엽니다.

### 2단계: 실제 값으로 수정

다음 항목들을 실제 값으로 변경하세요:

```bash
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=52f6bdf210f08fbb83c9d694715de82dae1d3a7d56dbf267b3623e9ddec1e9a5  # ✅ 이미 설정됨

# OpenAI Configuration (선택사항)
OPENAI_API_KEY=sk-your-actual-openai-key-here
OPENAI_MODEL=gpt-4

# Jira Configuration (필수)
JIRA_BASE_URL=https://your-company.atlassian.net  # ⚠️ 실제 Jira URL로 변경
JIRA_PAT=your-actual-jira-personal-access-token   # ⚠️ 실제 PAT로 변경

# Confluence Configuration (필수)
CONFLUENCE_BASE_URL=https://your-company.atlassian.net  # ⚠️ 실제 Confluence URL로 변경
CONFLUENCE_PAT=your-actual-confluence-personal-access-token  # ⚠️ 실제 PAT로 변경
```

### 3단계: Atlassian 정보 확인

#### Jira/Confluence URL 형식
- **클라우드:** `https://your-company.atlassian.net`
- **서버/데이터센터:** `https://jira.your-company.com` 또는 `https://confluence.your-company.com`

#### Personal Access Token (PAT) 생성

**Jira PAT 생성:**
1. Jira 로그인
2. 프로필 아이콘 클릭 → **Profile**
3. **Personal Access Tokens** 메뉴
4. **Create Token** 클릭
5. 토큰 이름 입력 후 생성
6. 생성된 토큰 복사 (한 번만 표시됨!)

**Confluence PAT 생성:**
1. Confluence 로그인
2. 프로필 아이콘 클릭 → **환경설정** (Settings)
3. **개인용 액세스 토큰** (Personal Access Tokens)
4. **토큰 만들기** (Create Token)
5. 토큰 이름 입력 후 생성
6. 생성된 토큰 복사

### 4단계: 서버 재시작

`.env` 파일 수정 후 서버를 재시작해야 합니다:

1. 현재 실행 중인 터미널에서 `Ctrl+C` 입력
2. `Run_production.bat` 다시 실행

## 예시 설정

```bash
# 실제 설정 예시 (회사 정보에 맞게 수정)
FLASK_ENV=production
SECRET_KEY=52f6bdf210f08fbb83c9d694715de82dae1d3a7d56dbf267b3623e9ddec1e9a5

JIRA_BASE_URL=https://mycompany.atlassian.net
JIRA_PAT=ATATT3xFfGF0abcdefghijklmnopqrstuvwxyz1234567890

CONFLUENCE_BASE_URL=https://mycompany.atlassian.net
CONFLUENCE_PAT=ATATT3xFfGF0abcdefghijklmnopqrstuvwxyz1234567890
```

## 보안 주의사항

⚠️ **중요:**
- PAT는 비밀번호와 동일한 수준의 보안이 필요합니다
- `.env` 파일을 절대 Git에 커밋하지 마세요
- PAT가 유출되면 즉시 폐기하고 새로 생성하세요
- 정기적으로 PAT를 갱신하세요

## 문제 해결

### 여전히 404 에러가 발생하는 경우

1. **URL 확인:** 브라우저에서 Jira/Confluence URL에 직접 접속 가능한지 확인
2. **PAT 권한 확인:** PAT에 필요한 권한이 있는지 확인
3. **네트워크 확인:** 회사 방화벽이나 VPN 설정 확인
4. **로그 확인:** `logs/error.log` 파일에서 상세 에러 확인

### 401 Unauthorized 에러

- PAT가 잘못되었거나 만료됨
- 새 PAT를 생성하여 다시 설정

### 403 Forbidden 에러

- PAT에 필요한 권한이 없음
- 관리자에게 권한 요청 필요

---

**다음 단계:**
1. `.env` 파일 수정
2. 서버 재시작 (`Ctrl+C` 후 `Run_production.bat`)
3. 브라우저에서 다시 테스트
