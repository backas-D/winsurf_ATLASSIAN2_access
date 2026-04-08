## 1. 프로젝트 개요
이 프로젝트는 사용자의 요청에 따라 Atlassian 제품군(Confluence, Jira 등)의 접근을 위한 프로젝트입니다.

## 2. 프로젝트 목표
- 사용자의 요청에 따라 Jira 및 Confluence 접속하여 요청한 페이지를 오픈한다. 
- 사용자의 요청에 따라 Confluence 페이지에 내용을 추가하거나, 파일을 업로드한다.
- 사용자의 요청에 따라 Jira 이슈를 생성하거나, 수정한다.

## 3. SW stack
- Python 3.13
- Flask 3.1.0
- extract-msg 0.55.0
- SQLite
- HTML/CSS
- Windows Batch
- OpenAI API
- Atlassian API
- node.js
- npm

## 4. 디렉터리 및 파일 구조
- root
  └ Data 폴더 : RQMT파일을 저장 및 업로드를 위해 사용하는 폴더
- main.py
- frontend.py
- backend.py
- requirements.txt
- Run_app.bat
- .env
- ignore.env
- .tmp
- .venv


## 5. Frontend 형식
- HTML/CSS로 구현
- Flask를 사용하여 웹 애플리케이션으로 실행
- 애플의 제품설명 홈페이지 스타일을 참고하여 GUI를 구성한다.
- GUI는 다음과 같이 사이드바와 메인화면으로 구성된다.
- 사이드바에는 다음과 같은 항목이 있다.
  - 프로젝트 이름 입력창과 **Confluence 페이지 검색** 버튼
  - 프로젝트 이름 입력창과 **Jira 이슈 검색** 버튼
  
- 메인화면에는 다음과 같은 항목이 있다.
  - **Confluence 페이지 검색** 내용 결과창
    - **Confluence 페이지 검색** 버튼 클릭의 결과를 표시한다.
    - 해당 프로젝트의 **하위 트리구조를 모두 표시**한다.
    - 표시된 하위트리구조의 각 폴더를 클릭하면 해당 해당 Confluence 페이지를 브라우저에서 오픈한다.   
  - **Jira 이슈 검색** 내용 결과창
    - **Jira 이슈 검색** 버튼 클릭의 결과를 표시한다.
    - 해당 프로젝트의 **Jira 이슈 목록을 모두 표시**한다.
    - 표시된 Jira 이슈 목록의 각 이슈를 클릭하면 해당 해당 Jira WBS 페이지를 브라우저에서 오픈한다.
  

## 6. 참고 자료
- [ATLASSIAN2 구조 문서](../ATLASSIAN2/structure.md)
- [ATLASSIAN2 아키텍처 문서](../ATLASSIAN2/architecture.md)

## 7. 추가 사항
- 추가 내용은 직전 개선확인 이후 새롭게 변경된 사항만을 이 파일에 반영한다.
- 추가 기록에는 반드시 버전과 날짜를 함께 표시한다.
- 버전 표기는 예시와 같이 관리한다.
  - `v1.0.0 - 2026-03-24`
- 개선확인으로 추가되는 내용은 누적 기록 방식으로 관리한다.
- "Run_app.bat" 파일을 실행하여 애플리케이션을 실행한다.
- **개선확인**이라고 프롬프트에 쓰면, 현재 기준 추가 개선된 부분을 정리하여 이 파일에 추가한다.

---

## 8. 개선 이력

### v1.0.0 - 2026-03-31 (프로덕션 배포 구성)

#### 8.1 프로덕션 배포 환경 구축
- **Waitress WSGI 서버 도입**
  - Windows 환경에 최적화된 프로덕션 WSGI 서버 적용
  - 멀티스레드 지원 (4 threads)
  - 외부 접근 허용 (`0.0.0.0:5000` 바인딩)

- **프로덕션 실행 스크립트 추가**
  - `Run_production.bat` 생성
  - 자동 의존성 설치
  - 로그 파일 자동 생성 및 관리
  - 웹브라우저 자동 실행 기능

#### 8.2 보안 강화
- **환경별 설정 분리**
  - 개발/프로덕션 모드 분리 (`FLASK_ENV` 환경 변수)
  - SECRET_KEY 환경 변수 관리
  - `.env.production.example` 템플릿 제공

- **보안 헤더 추가**
  - X-Content-Type-Options: nosniff
  - X-Frame-Options: SAMEORIGIN
  - X-XSS-Protection: 1; mode=block

- **환경 변수 관리**
  - python-dotenv 라이브러리 추가
  - SECRET_KEY 자동 생성 가이드 제공
  - API 키 보안 관리 강화

#### 8.3 로깅 시스템 구축
- **자동 로그 로테이션**
  - 애플리케이션 로그: `logs/app.log`
  - 에러 로그: `logs/error.log`
  - 프로덕션 서버 로그: `logs/production_*.log`
  - 최대 파일 크기: 10MB
  - 백업 파일 수: 10개

- **로그 레벨 관리**
  - 프로덕션: INFO 레벨
  - 개발: DEBUG 레벨
  - 에러 로그 분리 관리

#### 8.4 네트워크 및 방화벽 설정
- **Windows 방화벽 자동 설정 스크립트**
  - `setup_firewall.ps1` 생성
  - 포트 5000 자동 개방
  - IP 범위 제한 옵션 제공
  - 관리자 권한 자동 확인

- **외부 접근 지원**
  - 로컬호스트 접근
  - 내부 네트워크 접근
  - 외부 인터넷 접근 (포트 포워딩 필요)

#### 8.5 배포 문서화
- **상세 배포 가이드 작성**
  - `DEPLOYMENT.md`: 전체 배포 가이드
  - `QUICKSTART.md`: 빠른 시작 가이드 (8분 완료)
  - `ENV_SETUP_GUIDE.md`: 환경 설정 가이드
  - `DEPLOYMENT_STATUS.md`: 배포 상태 보고서
  - `DEPLOYMENT_SUMMARY.md`: 배포 요약

- **트러블슈팅 가이드**
  - 일반적인 문제 해결 방법
  - API 연결 실패 대응
  - 방화벽 설정 문제 해결
  - 로그 확인 방법

#### 8.6 배포 패키지 자동화
- **배포 패키지 생성 스크립트**
  - `create_distribution_package.ps1` 생성
  - 필요한 파일만 자동 선별
  - 민감 정보 자동 제외 (.env, logs, db 등)
  - ZIP 패키지 자동 생성

- **배포 패키지 구성**
  - 애플리케이션 소스 코드
  - 실행 스크립트 (Run_production.bat, Run_app.bat)
  - 방화벽 설정 스크립트
  - 환경 변수 템플릿
  - 설치 가이드 (INSTALL.md 자동 생성)
  - 버전 정보 (version.json)

- **배포 가이드 문서**
  - `DISTRIBUTION_GUIDE.md`: 배포 절차 상세 가이드
  - 사용자별 설정 방법
  - 보안 주의사항
  - 버전 관리 방법

#### 8.7 디렉터리 및 파일 구조 업데이트
```
root/
├── Data/                           # 데이터 저장 폴더
├── logs/                           # 로그 파일 (자동 생성)
├── static/                         # 정적 파일
├── templates/                      # HTML 템플릿
├── .venv/                          # Python 가상환경
├── .tmp/                           # 임시 파일
├── dist/                           # 배포 패키지 (자동 생성)
├── main.py                         # 메인 애플리케이션
├── frontend.py                     # 프론트엔드 라우팅
├── backend.py                      # 백엔드 로직
├── requirements.txt                # Python 의존성
├── Run_app.bat                     # 개발 모드 실행
├── Run_production.bat              # 프로덕션 모드 실행
├── setup_firewall.ps1              # 방화벽 설정 스크립트
├── create_distribution_package.ps1 # 배포 패키지 생성 스크립트
├── .env                            # 환경 변수 (gitignore)
├── .env.production.example         # 환경 변수 템플릿
├── .gitignore                      # Git 제외 목록
├── project_data.db                 # SQLite 데이터베이스
├── README.md                       # 프로젝트 문서
├── QUICKSTART.md                   # 빠른 시작 가이드
├── DEPLOYMENT.md                   # 배포 가이드
├── DEPLOYMENT_SUMMARY.md           # 배포 요약
├── DEPLOYMENT_STATUS.md            # 배포 상태
├── ENV_SETUP_GUIDE.md              # 환경 설정 가이드
├── DISTRIBUTION_GUIDE.md           # 배포 패키지 가이드
└── project_access.md               # 프로젝트 접근 문서
```

#### 8.8 SW Stack 업데이트
- **추가된 라이브러리**
  - waitress >= 2.1.2 (프로덕션 WSGI 서버)
  - python-dotenv >= 1.0.0 (환경 변수 관리)

- **기존 라이브러리**
  - Python 3.13
  - Flask 3.1.0
  - extract-msg 0.55.0
  - SQLite
  - OpenAI API
  - Atlassian API

#### 8.9 실행 방법 업데이트
- **개발 모드**: `Run_app.bat` (로컬호스트만, debug=True)
- **프로덕션 모드**: `Run_production.bat` (외부 접근 허용, debug=False)
- **방화벽 설정**: `setup_firewall.ps1` (관리자 권한 필요)

#### 8.10 배포 완료 상태
- ✅ 프로덕션 서버 구성 완료
- ✅ 보안 설정 완료
- ✅ 로깅 시스템 구축 완료
- ✅ 배포 문서화 완료
- ✅ 배포 패키지 자동화 완료
- ✅ 외부 접근 지원 완료
- ⚠️ 사용자별 API 키 설정 필요 (.env 파일)
- ⚠️ 방화벽 설정 필요 (관리자 권한)
- ⚠️ HTTPS 설정 권장 (프로덕션 환경) 
