# ALM MCP (stdio)

Windsurf, Codex 등 AI 도구에서 로컬 stdio MCP 서버를 통해 ALM(Jira + Confluence + Bitbucket + Codebeamer) REST API를 사용할 수 있게 해주는 도구입니다.

---

## Quick Start (사용자)

### 1) ZIP 다운로드

- 최신 `alm-mcp-stdio-<version>-win.zip` 파일 다운로드
  - https://bitbucket.hlklemove.com/users/seunghyun.ko/repos/alm_mcp_stdio/browse/release

### 2) 압축 해제

- 예) `C:\Tools\alm-mcp-stdio\` 같은 경로에 압축 해제

### 3) 필수 설정

- Node.js 18+ 설치 (간편: Windows 설치 프로그램 (.msi))
  - https://nodejs.org/ko/download
- `.env` 설정
  - `.env.example`을 복사해서 `.env` 생성
  - `.env`에 `JIRA_BASE_URL`, `JIRA_PAT` 입력
  - Jira PAT 생성 경로: Jira > Profile > Personal Access Tokens > Create Token
  - Confluence 사용 시: `.env`에 `CONFLUENCE_BASE_URL`, `CONFLUENCE_PAT` 입력
    - Confluence PAT 생성 경로: Confluence > 환경설정 > 개인용 액세스 토큰 > 토큰 만들기
  - Bitbucket 사용 시: `.env`에 `BITBUCKET_BASE_URL`, `BITBUCKET_TOKEN` 입력
    - Bitbucket PAT 생성 경로: Bitbucket > Manage account > HTTP access tokens > create token
  - Codebeamer 사용 시: `.env`에 `CODEBEAMER_BASE_URL`, `CODEBEAMER_USERNAME`, `CODEBEAMER_PASSWORD` 입력
    - 기본은 kill-switch가 꺼져 있으므로, 사용하려면 `CODEBEAMER_TOOLS_ENABLED=true`도 설정하세요.

  - 추가 설정(권한/안전정책/툴 on/off)은 `.env.example`에 템플릿이 모두 정리되어 있습니다.

주의:

- `JIRA_PAT`, `CONFLUENCE_PAT` , `BITBUCKET_TOKEN`, `CODEBEAMER_PASSWORD`는 **외부 유출 금지** (개인/사내 시스템 접근 권한)

### 4) MCP 등록

동작 확인:
- Windsurf(Cascade)
- Codex CLI
- Codex IDE
- Codex APP

---
## Codex APP 설정

설정 > MCP 서버 > 서버 추가

<details>
<summary><strong>Codex APP Setting (이미지)</strong></summary>

![Codex MCP Settings](Codex_APP_Setting.png)

</details>

---

## Codex IDE 설정

<details>
<summary><strong>Codex IDE Setting (이미지)</strong></summary>

![Codex MCP Settings](Codex_IDE_Setting.png)

</details>

---

## Codex CLI 설정

`.env`가 준비된 상태에서 아래를 실행합니다.

```powershell
codex mcp add ALM_MCP_STDIO -- node "<ZIP_압축해제_경로>\dist\index.js"
codex mcp list
codex mcp get ALM_MCP_STDIO
```

예)

```powershell
codex mcp add ALM_MCP_STDIO -- node "C:\Tools\alm-mcp-stdio\dist\index.js"
```

---

## Windsurf(Cascade) 설정

문서: https://docs.windsurf.com/windsurf/cascade/mcp

Windsurf Settings > Cascade > MCP Servers > Open MCP Marketplace

<details>
<summary><strong>Windsurf MCP Settings (이미지)</strong></summary>

![Windsurf MCP Settings](windsurf_setting.png)

</details>

MCP 설정 파일(`mcp_config.json`)에 아래처럼 등록합니다.

```json
{
  "mcpServers": {
    "ALM_MCP_STDIO": {
      "command": "node",
      "args": [
        "C:\\Tools\\alm-mcp-stdio\\dist\\index.js"
      ]
    }
  }
}
```

- `args`는 압축 해제한 폴더의 `dist\\index.js` **절대경로**로 바꿔주세요.
- MCP 서버는 `dist` 상위 폴더의 `.env`를 읽어서 동작합니다.

---

## 사용하기

Windsurf(Cascade)에서 아래처럼 요청하면 됩니다:

<details>
<summary><strong>사용 예시 (이미지)</strong></summary>

![alt text](image.png)

![alt text](image-1.png)

</details>

- `IDA-3862` 내용을 요약해줘
- Jira 에서  IDA 프로젝트의 최근 이슈 10개 찾아줘

---

## 제공 tools

### Read tools (기본 허용)

Read 툴은 기본적으로 안전하지만, 응답이 커지면 모델 컨텍스트/토큰을 많이 사용합니다.  
가능하면 `fields`/`expand` 옵션을 사용해서 **필요한 정보만** 가져오는 것을 권장합니다.

<details>
<summary><strong>Jira Read tools</strong></summary>

- `jira_search_issues`
  - **권한**: Read
  - **설명**: JQL로 이슈 검색
  - **입력**: `jql`, `startAt?`, `maxResults?`, `fields?`, `expand?`
- `jira_get_issue`
  - **권한**: Read
  - **설명**: 이슈 상세 조회
  - **입력**: `issueKey`, `fields?`, `expand?`
- `jira_get_issue_editmeta`
  - **권한**: Read
  - **설명**: 이슈 수정 가능 필드/허용값 조회(editmeta)
  - **입력**: `issueKey`
- `jira_get_issue_editmeta_slim`
  - **권한**: Read
  - **설명**: editmeta를 요약(slim)해서 반환(모델 효율/토큰 절감)
  - **입력**: `issueKey`
- `jira_get_issue_rendered`
  - **권한**: Read
  - **설명**: 렌더링된 필드(renderedFields) 조회(HTML)
  - **입력**: `issueKey`, `fields?`
- `jira_get_issue_comments`
  - **권한**: Read
  - **설명**: 이슈 댓글 목록 조회
  - **입력**: `issueKey`, `startAt?`, `maxResults?`
- `jira_get_issue_worklog`
  - **권한**: Read
  - **설명**: 이슈 worklog(시간 기록) 조회
  - **입력**: `issueKey`, `startAt?`, `maxResults?`
- `jira_get_issue_watchers`
  - **권한**: Read
  - **설명**: 이슈 watchers 조회
  - **입력**: `issueKey`
- `jira_get_issue_changelog`
  - **권한**: Read
  - **설명**: 이슈 변경 이력(changelog) 조회
  - **입력**: `issueKey`, `fields?`
- `jira_get_issue_transitions`
  - **권한**: Read
  - **설명**: 이슈 상태 전환(transition) 후보 목록 조회
  - **입력**: `issueKey`
- `jira_get_project`
  - **권한**: Read
  - **설명**: 프로젝트 정보 조회
  - **입력**: `projectKey`
- `jira_get_project_components`
  - **권한**: Read
  - **설명**: 프로젝트 컴포넌트 목록 조회
  - **입력**: `projectKey`
- `jira_get_project_versions`
  - **권한**: Read
  - **설명**: 프로젝트 버전 목록 조회
  - **입력**: `projectKey`
- `jira_get_myself`
  - **권한**: Read
  - **설명**: 현재 PAT로 인증된 사용자 정보 조회

- `jira_get_server_info`
  - **권한**: Read
  - **설명**: Jira 서버 정보(버전/빌드 등) 조회

- `jira_get_fields`
  - **권한**: Read
  - **설명**: Jira 필드 목록 조회(`customfield_XXXXX` 매핑에 유용)

- `jira_get_priorities`
  - **권한**: Read
  - **설명**: Jira priority 목록 조회

- `jira_get_statuses`
  - **권한**: Read
  - **설명**: Jira status 목록 조회

- `jira_get_resolutions`
  - **권한**: Read
  - **설명**: Jira resolution 목록 조회

- `jira_get_issue_types`
  - **권한**: Read
  - **설명**: Jira issue type 목록 조회

- `jira_get_issue_link_types`
  - **권한**: Read
  - **설명**: Jira issue link type 목록 조회

- `jira_get_create_meta`
  - **권한**: Read
  - **설명**: 이슈 생성 메타데이터 조회(프로젝트/이슈타입/필수필드)
  - **입력**: `projectKeys?`, `issueTypeNames?`, `expand?`

- `jira_search_users`
  - **권한**: Read
  - **설명**: 사용자 검색(assignee 설정 등에 유용)
  - **입력**: `username`, `maxResults?`

</details>

#### Confluence Read tools

<details>
<summary><strong>Confluence Read tools</strong></summary>

- `confluence_get_myself`
  - **권한**: Read
  - **설명**: 현재 PAT로 인증된 Confluence 사용자 정보 조회

- `confluence_list_spaces`
  - **권한**: Read
  - **설명**: Confluence space 목록 조회
  - **입력**: `startAt?`, `limit?`, `expand?`

- `confluence_get_content_by_title`
  - **권한**: Read
  - **설명**: space + title로 content 조회(제목 정확히 일치)
  - **입력**: `spaceKey`, `title`, `type?`, `startAt?`, `limit?`, `expand?`

- `confluence_search_content`
  - **권한**: Read
  - **설명**: CQL로 Confluence 컨텐츠 검색
  - **입력**: `cql`, `startAt?`, `limit?`, `expand?`

  예시(CQL):

  - 스페이스 내 페이지 검색: `space = AO AND type = page AND text ~ "release"`
  - 제목으로 검색: `title ~ "RN" AND type = page`

- `confluence_get_content`
  - **권한**: Read
  - **설명**: contentId로 컨텐츠 조회
  - **입력**: `contentId`, `expand?`

- `confluence_get_page`
  - **권한**: Read
  - **설명**: pageId(contentId)로 페이지 조회(기본 expand: `space,version,body.view`)
  - **입력**: `pageId`, `expand?`

- `confluence_get_space`
  - **권한**: Read
  - **설명**: spaceKey로 스페이스 정보 조회
  - **입력**: `spaceKey`, `expand?`

- `confluence_get_page_children`
  - **권한**: Read
  - **설명**: 특정 페이지의 자식 페이지 목록 조회
  - **입력**: `pageId`, `startAt?`, `limit?`, `expand?`

- `confluence_get_page_versions`
  - **권한**: Read
  - **설명**: 특정 페이지의 버전 이력 조회
  - **입력**: `pageId`, `startAt?`, `limit?`

- `confluence_get_page_attachments`
  - **권한**: Read
  - **설명**: 특정 페이지의 첨부파일 목록 조회
  - **입력**: `pageId`, `startAt?`, `limit?`, `expand?`

- `confluence_get_page_labels`
  - **권한**: Read
  - **설명**: 특정 페이지의 라벨 목록 조회
  - **입력**: `pageId`, `startAt?`, `limit?`, `prefix?`

- `confluence_get_page_comments`
  - **권한**: Read
  - **설명**: 특정 페이지의 댓글 목록 조회
  - **입력**: `pageId`, `startAt?`, `limit?`, `expand?`

</details>

#### Bitbucket Read tools

<details>
<summary><strong>Bitbucket Read tools</strong></summary>

- `bitbucket_test_auth`
  - **권한**: Read
  - **설명**: Bitbucket 인증 테스트(프로젝트 목록 조회)

- `bitbucket_list_projects`
  - **권한**: Read
  - **설명**: Bitbucket 프로젝트 목록 조회

- `bitbucket_list_repos_by_project`
  - **권한**: Read
  - **설명**: 프로젝트 내 레포 목록 조회
  - **입력**: `projectKey`, `start?`, `limit?`

- `bitbucket_get_repo`
  - **권한**: Read
  - **설명**: 레포 상세 조회
  - **입력**: `projectKey`, `repoSlug`

- `bitbucket_list_branches`
  - **권한**: Read
  - **설명**: 브랜치 목록 조회
  - **입력**: `projectKey`, `repoSlug`, `filterText?`, `start?`, `limit?`

- `bitbucket_list_commits`
  - **권한**: Read
  - **설명**: 커밋 목록 조회
  - **입력**: `projectKey`, `repoSlug`, `path?`, `since?`, `until?`, `start?`, `limit?`

- `bitbucket_list_tags`
  - **권한**: Read
  - **설명**: 태그 목록 조회
  - **입력**: `projectKey`, `repoSlug`, `filterText?`, `start?`, `limit?`

- `bitbucket_get_raw_file`
  - **권한**: Read
  - **설명**: 레포 내 파일 raw 조회
  - **입력**: `projectKey`, `repoSlug`, `filePath`, `at?`

</details>

#### Codebeamer Read tools

<details>
<summary><strong>Codebeamer Read tools</strong></summary>

- `codebeamer_get_item`
  - **권한**: Read
  - **설명**: itemId로 item 조회
  - **입력**: `itemId`
- `codebeamer_get_item_children`
  - **권한**: Read
  - **설명**: itemId 기준 자식 item 목록 조회
  - **입력**: `itemId`
- `codebeamer_search_items_cbql`
  - **권한**: Read
  - **설명**: cbQL로 item 검색
  - **입력**: `queryString`, `page?`, `pageSize?`, `baselineId?`
- `codebeamer_search_items_cbql_advanced`
  - **권한**: Read
  - **설명**: request body 기반 cbQL 검색
  - **입력**: `body`
- `codebeamer_list_association_types`
  - **권한**: Read
  - **설명**: association type 목록 조회
- `codebeamer_get_items_relations`
  - **권한**: Read
  - **설명**: item relation(upstream/downstream/association) 조회
  - **입력**: `body`, `baselineId?`
- `codebeamer_get_association`
  - **권한**: Read
  - **설명**: associationId로 association 조회
  - **입력**: `associationId`
- `codebeamer_get_association_history`
  - **권한**: Read
  - **설명**: association 변경 이력 조회
  - **입력**: `associationId`, `page?`, `pageSize?`

</details>

---

### Write tools (기본 차단)

쓰기 툴은 안전을 위해 기본값이 **차단**이며,

- `dryRun`이 기본적으로 `true`로 동작하고
- 실제 수행은 `confirm=true`가 필요하며
- 전역/툴별 설정으로 권한을 열어야 합니다.

<details>
<summary><strong>Write tools 목록</strong></summary>

- `jira_add_comment`
  - **권한**: Write
  - **설명**: 이슈에 댓글 추가
  - **입력**: `issueKey`, `comment`, `dryRun?`, `confirm?`
- `jira_transition_issue`
  - **권한**: Write
  - **설명**: 이슈 상태 전환
  - **입력**: `issueKey`, `transitionId`, `comment?`, `dryRun?`, `confirm?`
- `jira_assign_issue`
  - **권한**: Write
  - **설명**: 이슈 담당자 할당
  - **입력**: `issueKey`, `assignee`, `dryRun?`, `confirm?`
- `jira_update_issue_fields`
  - **권한**: Write
  - **설명**: 이슈 필드 업데이트(현재는 `summary`/`description`만)
  - **입력**: `issueKey`, `summary?`, `description?`, `dryRun?`, `confirm?`
- `jira_create_issue`
  - **권한**: Write
  - **설명**: 이슈 생성
  - **입력**: `projectKey`, `issueType`, `summary`, `description?`, `dryRun?`, `confirm?`

- `confluence_create_page`
  - **권한**: Write
  - **설명**: Confluence 페이지 생성
  - **입력**: `spaceKey`, `title`, `bodyStorage`, `ancestorId?`, `dryRun?`, `confirm?`

- `confluence_update_page`
  - **권한**: Write
  - **설명**: Confluence 페이지 수정(title/body)
  - **입력**: `pageId`, `title?`, `bodyStorage?`, `versionMessage?`, `dryRun?`, `confirm?`

- `confluence_add_page_comment`
  - **권한**: Write
  - **설명**: Confluence 페이지에 댓글 추가
  - **입력**: `pageId`, `bodyStorage`, `dryRun?`, `confirm?`

- `codebeamer_update_item`
  - **권한**: Write
  - **설명**: Codebeamer item 업데이트
  - **입력**: `itemId`, `body`, `dryRun?`, `confirm?`
- `codebeamer_patch_item_children`
  - **권한**: Write
  - **설명**: item children patch
  - **입력**: `itemId`, `mode`, `childItemId`, `index`, `dryRun?`, `confirm?`
- `codebeamer_delete_item`
  - **권한**: Write
  - **설명**: item 삭제(휴지통 이동)
  - **입력**: `itemId`, `dryRun?`, `confirm?`
- `codebeamer_bulk_update_item_fields`
  - **권한**: Write
  - **설명**: item field bulk update
  - **입력**: `body`, `atomic?`, `dryRun?`, `confirm?`

- `codebeamer_create_association`
  - **권한**: Write
  - **설명**: association 생성
  - **입력**: `body`, `dryRun?`, `confirm?`
- `codebeamer_update_association`
  - **권한**: Write
  - **설명**: association 업데이트
  - **입력**: `associationId`, `body`, `dryRun?`, `confirm?`
- `codebeamer_delete_association`
  - **권한**: Write
  - **설명**: association 삭제
  - **입력**: `associationId`, `dryRun?`, `confirm?`

</details>

---

## 쓰기 안전정책

기본값은 안전을 위해 **쓰기 차단**입니다.

`dryRun`/`confirm` 개념:

- `dryRun=true`
  - 실제 Jira에 변경을 **하지 않고**, "무슨 작업을 할지"만 미리보기 형태로 반환합니다.
- `dryRun=false`
  - 실제 변경을 시도합니다. 단, 아래 조건을 모두 만족해야 실행됩니다.
- `confirm=true`
  - 사람이 의도적으로 실행하겠다는 확인 플래그입니다. 기본 정책에서는 `confirm=true`가 없으면 write는 차단됩니다.

설정 방법(권장):

- `.env.example`을 그대로 복사한 뒤(`.env` 생성), 필요한 항목만 **주석(#)을 해제**해서 사용하세요.
- `.env.example`는 아래 순서로 구성되어 있습니다:
  - Global policy: 전체 kill-switch / read-write 허용 / 전역 안전정책
  - Tool-default policy: "모든 tool"에 공통 적용되는 기본값
  - Per-tool overrides: 접두사(prefix)로 개별 tool만 따로 설정

### 전역 설정(.env)

- `JIRA_TOOLS_ENABLED=false`
  - 모든 툴 차단
- `JIRA_READ_ENABLED=false`
  - read 툴 차단
- `JIRA_WRITE_ENABLED=false`
  - write 툴 실제 실행 차단(기본값)
- `JIRA_WRITE_DRYRUN_DEFAULT=true`
  - write 툴의 `dryRun` 기본값(기본 true)
- `JIRA_WRITE_REQUIRE_CONFIRM=true`
  - write 툴 실행에 `confirm=true` 요구(기본 true)
- `JIRA_WRITE_FORCE_DRYRUN=true`
  - 모든 write 툴을 강제로 dry-run 모드로 고정
- `JIRA_ALLOWED_PROJECTS=IDA,ABC`
  - write 툴이 허용되는 프로젝트 allowlist

주의:

- `JIRA_ALLOWED_PROJECTS`가 **비어있으면** allowlist 제한이 적용되지 않습니다. 즉, 프로젝트 제한 없이 동작합니다.

### 툴별 설정(.env)

툴별로 on/off, allowlist, dry-run 기본값 등을 오버라이드할 수 있습니다.

- 접두사 규칙: `jira_add_comment` -> `JIRA_TOOL_JIRA_ADD_COMMENT`
- `.env.example` 하단에 각 tool별 prefix가 **미리 정의된 템플릿**으로 나열되어 있으니, 필요한 tool만 주석을 해제해서 쓰면 됩니다.

추가로, 모든 tool에 적용되는 기본값(툴별 override가 없을 때 사용되는 값)을 설정할 수 있습니다:

- `JIRA_TOOL_DEFAULT_ENABLED`
- `JIRA_TOOL_DEFAULT_WRITE_ENABLED`
- `JIRA_TOOL_DEFAULT_DRYRUN_DEFAULT`
- `JIRA_TOOL_DEFAULT_REQUIRE_CONFIRM`
- `JIRA_TOOL_DEFAULT_ALLOWED_PROJECTS`

- 공통 키:
  - `_ENABLED=true|false`
  - `_WRITE_ENABLED=true|false`
  - `_DRYRUN_DEFAULT=true|false`
  - `_REQUIRE_CONFIRM=true|false`
  - `_ALLOWED_PROJECTS=IDA,ABC`

쓰기 허용이 꼭 필요하면, 설치 폴더의 `.env`에서 아래를 직접 수정하세요:

- `JIRA_WRITE_ENABLED=true`
- (권장) `JIRA_ALLOWED_PROJECTS=IDA,ABC`

예시: 댓글 쓰기를 실제로 허용(권장 최소 설정)

1) `.env`에서 전역 write 허용

- `JIRA_WRITE_ENABLED=true`
- `JIRA_ALLOWED_PROJECTS=IDA`

2) 요청 시

- 미리보기: `dryRun=true` (기본값)
- 실제 실행: `dryRun=false` + `confirm=true`

예시: 댓글만 실제 허용하고(다른 write는 그대로 차단/미리보기 유지)

- 전역 write 허용 + 프로젝트 제한
  - `JIRA_WRITE_ENABLED=true`
  - `JIRA_ALLOWED_PROJECTS=IDA`

- (선택) 댓글 tool만 따로 세부 정책 지정
  - `JIRA_TOOL_JIRA_ADD_COMMENT_WRITE_ENABLED=true`
  - `JIRA_TOOL_JIRA_ADD_COMMENT_DRYRUN_DEFAULT=true`
  - `JIRA_TOOL_JIRA_ADD_COMMENT_REQUIRE_CONFIRM=true`

---

## (유지보수자용) Release ZIP 만들기

레포 루트에서:

### 빌드만 하기

```powershell
npm ci
npm run build
```

### Release ZIP 만들기

```powershell
PowerShell -ExecutionPolicy Bypass -File .\make-release.ps1
```