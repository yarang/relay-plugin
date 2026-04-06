# /relay:import-templates

다른 프로젝트에서 내보낸 템플릿을 현재 프로젝트의 project scope로 가져옵니다.

## 사용법

```text
/relay:import-templates {경로}
```

- `{경로}`: 디렉토리 또는 `.tar.gz` 아카이브 경로

경로를 지정하지 않으면 입력을 요청합니다.

## 사전 확인

1. `.claude/relay/` 디렉토리가 존재하는지 확인 (없으면 `/relay:setup` 먼저 실행 안내)
2. 지정 경로에 `relay-templates-export.json` 메타데이터 파일이 있는지 확인
3. 아카이브인 경우 임시 디렉토리에 압축 해제 후 진행

## 충돌 감지

`.claude/relay/templates/` 에 동일 `id`의 파일이 이미 존재하면 충돌 목록을 표시합니다:

```text
⚠️ 아래 파일이 이미 존재합니다:

  modules/specs/auth-jwt.md
  modules/policies/blog-default.md

처리 방법을 선택하세요:
  [1] skip      — 기존 파일 유지, 충돌 파일 건너뜀
  [2] overwrite — 모두 덮어쓰기
  [3] rename    — 충돌 파일에 .imported 접미사 추가
  [4] cancel    — 가져오기 취소
```

## 가져오기 실행

선택에 따라 파일을 `.claude/relay/templates/` 하위에 복사합니다.

각 파일의 frontmatter에 `scope: project`가 없으면 자동으로 추가합니다.

## 완료 메시지

```text
✅ 템플릿 가져오기 완료

출처: {relay-templates-export.json의 source_project}
내보낸 날짜: {exported_at}

가져온 파일:
  specs     : {N}개
  platforms : {N}개
  policies  : {N}개
  definitions: {N}개
  건너뜀    : {N}개 (충돌)

적용된 위치: .claude/relay/templates/
```
