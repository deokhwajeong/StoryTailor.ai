# GitHub Projects 가이드

이 문서는 StoryTailor.ai 프로젝트의 GitHub Projects 보드를 설정하고 관리하는 방법을 설명합니다.

## 🚀 빠른 시작

### 1. GitHub CLI 설치

```bash
# macOS
brew install gh

# Windows
winget install --id GitHub.cli

# Ubuntu/Debian
sudo apt install gh
```

### 2. GitHub 인증

```bash
gh auth login
```

### 3. 백로그 Issues 생성

```bash
# 스크립트 실행 권한 부여
chmod +x scripts/create_backlog_issues.sh

# 스크립트 실행 (명령어 확인)
./scripts/create_backlog_issues.sh

# 출력된 gh issue create 명령어들을 복사하여 실행
```

## 📋 프로젝트 보드 설정

### GitHub Projects 접근

1. [GitHub Projects 페이지](https://github.com/users/deokhwajeong/projects/7/views/2) 접속
2. 또는 Repository → Projects 탭에서 접근

### Issues를 프로젝트에 추가하기

#### 방법 1: Issue 페이지에서 추가
1. Issues 탭에서 추가할 Issue 클릭
2. 오른쪽 사이드바에서 **Projects** 클릭
3. 프로젝트 선택

#### 방법 2: Projects 페이지에서 추가
1. Projects 페이지 열기
2. **+ Add items** 버튼 클릭
3. Repository의 Issues 검색/선택

### 보드 뷰 설정

#### 권장 뷰 설정

**Board View (보드 뷰)**
- To Do
- In Progress
- In Review
- Done

**Table View (테이블 뷰)**
- Priority (우선순위별 정렬)
- Phase (개발 단계별)
- Assignee (담당자별)

## 🏷️ 라벨 시스템

### 라벨 생성 명령어

```bash
# 우선순위 라벨
gh label create "priority:high" --color "d73a4a" --description "높은 우선순위"
gh label create "priority:medium" --color "fbca04" --description "중간 우선순위"
gh label create "priority:low" --color "0e8a16" --description "낮은 우선순위"

# 상태 라벨
gh label create "backlog" --color "5319e7" --description "백로그 항목"
gh label create "in-progress" --color "1d76db" --description "진행 중"
gh label create "in-review" --color "f9d0c4" --description "검토 중"

# 카테고리 라벨
gh label create "enhancement" --color "a2eeef" --description "새로운 기능"
gh label create "bug" --color "d73a4a" --description "버그 수정"
gh label create "documentation" --color "0075ca" --description "문서화"
```

## 📊 백로그 항목 목록

### 🔴 높은 우선순위 (High Priority)

| ID | 기능 | 예상 작업량 |
|----|------|------------|
| B-001 | 음성 읽기 기능 (TTS) | 2주 |
| B-002 | 음성 인식 기능 (STT) | 2주 |
| B-003 | 읽기 수준 진단 시스템 | 3주 |
| B-004 | AI 도서 추천 엔진 | 2주 |

### 🟡 중간 우선순위 (Medium Priority)

| ID | 기능 | 예상 작업량 |
|----|------|------------|
| B-005 | 분석 리포트 대시보드 | 3주 |
| B-006 | 프론트엔드 UI 완성 | 4주 |
| B-007 | 사용자 인증 시스템 | 2주 |
| B-008 | 이야기 저장 및 관리 | 1주 |

### 🟢 낮은 우선순위 (Low Priority)

| ID | 기능 | 예상 작업량 |
|----|------|------------|
| B-009 | 다국어 지원 | 2주 |
| B-010 | 부모 모니터링 기능 | 2주 |
| B-011 | 오프라인 모드 | 3주 |
| B-012 | 게이미피케이션 | 2주 |

## 🔄 워크플로우

### Issue 상태 변경

```
📌 To Do → 🚧 In Progress → 🔍 In Review → ✅ Done
```

### 스프린트 관리

1. **스프린트 계획**: 백로그에서 스프린트에 포함할 항목 선택
2. **스프린트 실행**: 항목들을 In Progress로 이동하며 작업
3. **스프린트 검토**: 완료된 항목 리뷰
4. **스프린트 회고**: 프로세스 개선점 도출

## 📝 관련 문서

- [BACKLOG.md](./BACKLOG.md) - 전체 백로그 목록
- [ROADMAP.md](./ROADMAP.md) - 프로젝트 로드맵
- [README.md](./README.md) - 프로젝트 개요

---

> 질문이나 제안이 있으시면 GitHub Issues를 통해 알려주세요!
