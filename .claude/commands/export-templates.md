# /relay:export-templates

프로젝트 scope 템플릿(`.claude/relay/templates/`)을 다른 프로젝트에서 재사용할 수 있도록 내보냅니다.

## 사전 확인

`.claude/relay/templates/` 디렉토리가 존재하는지 확인합니다.
없으면 아래 안내를 출력하고 중단합니다:

```text
⚠️ 내보낼 project scope 템플릿이 없습니다.

먼저 /relay:setup 을 실행하거나
.claude/relay/templates/ 에 커스텀 템플릿을 추가하세요.
```

## 내보내기 옵션 선택

```text
내보내기 형식을 선택하세요:

  [1] directory  — 지정 경로에 디렉토리로 복사
  [2] archive    — .tar.gz 아카이브로 패키징
  [3] preview    — 내보낼 파일 목록만 확인 (실제 내보내기 없음)
```

## 옵션별 처리

### [1] directory

출력 경로를 입력받습니다 (기본값: `./relay-templates-export/`).

다음 구조로 복사합니다:

```text
{출력경로}/
├── relay-templates-export.json   ← 메타데이터
├── definitions/
└── modules/
    ├── specs/
    ├── platforms/
    └── policies/
```

`relay-templates-export.json` 내용:

```json
{
  "exported_at": "{YYYY-MM-DDTHH:MM:SSZ}",
  "source_project": "{domain-config.json의 project_name}",
  "scope": "project",
  "files": ["{복사된 파일 목록}"]
}
```

### [2] archive

출력 파일명을 입력받습니다 (기본값: `relay-templates-{project_name}-{YYYYMMDD}.tar.gz`).

`relay-templates-export.json` 메타데이터를 포함하여 패키징합니다.

완료 후 출력:

```text
✅ 아카이브 생성 완료: {파일명}
   포함된 파일: {N}개
   크기: {size}
```

### [3] preview

내보낼 파일 목록을 출력합니다:

```text
내보낼 project scope 템플릿 목록:

  definitions/
    - {id}.md  (kind: composed-agent)
    ...
  modules/specs/
    - {id}.md  (type: spec)
    ...
  modules/platforms/
    - {id}.md  (type: platform)
    ...
  modules/policies/
    - {id}.md  (type: policy)
    ...

총 {N}개 파일
```

## 다른 프로젝트에서 가져오기

내보낸 템플릿을 다른 프로젝트에 적용하려면:

1. 내보낸 디렉토리 또는 아카이브를 대상 프로젝트로 복사
2. 파일들을 대상 프로젝트의 `.claude/relay/templates/` 아래에 배치
3. 각 파일의 frontmatter `scope: project` 확인

또는 `/relay:import-templates {경로}` 명령을 사용합니다.

## 완료 메시지 (directory/archive)

```text
✅ 템플릿 내보내기 완료

출력: {경로 또는 파일명}
포함된 모듈:
  specs     : {N}개
  platforms : {N}개
  policies  : {N}개
  definitions: {N}개

다른 프로젝트에 적용하려면:
  파일을 .claude/relay/templates/ 에 복사하거나
  /relay:import-templates {경로} 를 실행하세요.
```
