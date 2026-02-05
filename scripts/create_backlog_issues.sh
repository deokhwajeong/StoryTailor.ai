#!/bin/bash

# GitHub Issues 생성 스크립트
# 사용법: ./scripts/create_backlog_issues.sh
#
# 이 스크립트는 BACKLOG.md에 정의된 백로그 항목들을
# GitHub Issues로 생성하는 명령어들을 출력합니다.

set -e

REPO_URL="https://github.com/deokhwajeong/StoryTailor.ai"

echo "=== StoryTailor.ai 백로그 Issues 생성 ==="
echo ""

# GitHub CLI 설치 확인
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh)가 설치되어 있지 않습니다."
    echo "   설치 방법: https://cli.github.com/"
    echo ""
    echo "   macOS: brew install gh"
    echo "   Ubuntu: sudo apt install gh"
    echo "   Windows: winget install --id GitHub.cli"
    exit 1
fi

echo "✅ GitHub CLI 설치 확인됨: $(gh --version | head -1)"
echo ""

# GitHub 인증 확인
if ! gh auth status &> /dev/null; then
    echo "❌ GitHub 인증이 필요합니다."
    echo "   'gh auth login' 명령어로 인증해주세요."
    exit 1
fi

echo "✅ GitHub 인증 확인됨"
echo ""
echo "아래 명령어들을 복사하여 터미널에서 실행하세요."
echo ""
echo "=== 높은 우선순위 (High Priority) Issues ==="

# B-001: 음성 읽기 기능 (TTS)
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-001: 음성 읽기 기능 (TTS)" \\
  --body "## 📋 기능 설명
Text-to-Speech를 활용한 이야기 음성 출력 기능

## 🎯 목표
- 생성된 이야기를 음성으로 읽어주는 기능 구현
- 다양한 음성 옵션 제공 (남성/여성, 속도 조절)
- 감정 표현이 담긴 음성 생성

## 📊 우선순위
- [x] 🔴 높음 (High)

## 📅 예상 작업량
2주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] TTS API 통합 완료
- [ ] 음성 옵션 설정 기능 구현
- [ ] 프론트엔드 재생 UI 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 2" \\
  --label "backlog,enhancement,priority:high"
EOF

echo ""

# B-002: 음성 인식 기능 (STT)
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-002: 음성 인식 기능 (STT)" \\
  --body "## 📋 기능 설명
Speech-to-Text를 활용한 아이 음성 읽기 인식 기능

## 🎯 목표
- 아이가 이야기를 읽을 때 음성을 인식하는 기능 구현
- 아이 음성 인식 최적화
- 발음 정확도 피드백 제공

## 📊 우선순위
- [x] 🔴 높음 (High)

## 📅 예상 작업량
2주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] STT API 통합 완료
- [ ] 아이 음성 인식 정확도 80% 이상
- [ ] 발음 피드백 UI 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 2" \\
  --label "backlog,enhancement,priority:high"
EOF

echo ""

# B-003: 읽기 수준 진단 시스템
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-003: 읽기 수준 진단 시스템" \\
  --body "## 📋 기능 설명
Lexile 기반 읽기 능력 자동 평가 시스템

## 🎯 목표
- Lexile 기반 평가 알고리즘 개발
- 읽기 유창성 측정
- 어휘력 평가

## 📊 우선순위
- [x] 🔴 높음 (High)

## 📅 예상 작업량
3주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] Lexile 기반 평가 알고리즘 구현
- [ ] 읽기 유창성 측정 기능 구현
- [ ] 어휘력 평가 기능 구현
- [ ] 진단 결과 리포트 UI 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 2" \\
  --label "backlog,enhancement,priority:high"
EOF

echo ""

# B-004: AI 도서 추천 엔진
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-004: AI 도서 추천 엔진" \\
  --body "## 📋 기능 설명
진단 결과와 선호도 기반 AI 도서 추천 기능

## 🎯 목표
- 읽기 수준 기반 도서 추천
- 선호도 기반 도서 추천
- 학습 목표 기반 도서 추천

## 📊 우선순위
- [x] 🔴 높음 (High)

## 📅 예상 작업량
2주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] 추천 알고리즘 개발
- [ ] 도서 데이터베이스 구축
- [ ] 추천 결과 UI 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 3" \\
  --label "backlog,enhancement,priority:high"
EOF

echo ""
echo "=== 중간 우선순위 (Medium Priority) Issues ==="

# B-005: 분석 리포트 대시보드
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-005: 분석 리포트 대시보드" \\
  --body "## 📋 기능 설명
읽기 습관, 진도, 추천 등 상세 리포트 대시보드

## 🎯 목표
- 읽기 습관 분석
- 진도 추적
- 성장 리포트

## 📊 우선순위
- [x] 🟡 중간 (Medium)

## 📅 예상 작업량
3주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] 대시보드 UI 디자인
- [ ] 분석 데이터 API 개발
- [ ] 차트/그래프 시각화 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 3" \\
  --label "backlog,enhancement,priority:medium"
EOF

echo ""

# B-006: 프론트엔드 UI 완성
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-006: 프론트엔드 UI 완성" \\
  --body "## 📋 기능 설명
React 기반 사용자 인터페이스 완성

## 🎯 목표
- 반응형 디자인 구현
- 아동 친화적 UI/UX 디자인
- 접근성 지원 (WCAG 2.1)

## 📊 우선순위
- [x] 🟡 중간 (Medium)

## 📅 예상 작업량
4주

## 🚧 현재 상태
In Progress

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] 모든 주요 페이지 UI 완성
- [ ] 반응형 디자인 적용
- [ ] 접근성 테스트 통과
- [ ] 사용자 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 4" \\
  --label "backlog,enhancement,priority:medium,in-progress"
EOF

echo ""

# B-007: 사용자 인증 시스템
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-007: 사용자 인증 시스템" \\
  --body "## 📋 기능 설명
부모/아이 계정 분리 및 인증 시스템

## 🎯 목표
- 부모/아이 계정 분리
- 소셜 로그인 지원
- 안전한 인증 흐름

## 📊 우선순위
- [x] 🟡 중간 (Medium)

## 📅 예상 작업량
2주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] 회원가입/로그인 기능 구현
- [ ] 부모/아이 계정 분리 구현
- [ ] 소셜 로그인 통합
- [ ] 보안 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 4" \\
  --label "backlog,enhancement,priority:medium"
EOF

echo ""

# B-008: 이야기 저장 및 관리
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-008: 이야기 저장 및 관리" \\
  --body "## 📋 기능 설명
생성된 이야기 저장, 즐겨찾기, 공유 기능

## 🎯 목표
- 이야기 저장 기능
- 즐겨찾기 기능
- 공유 기능

## 📊 우선순위
- [x] 🟡 중간 (Medium)

## 📅 예상 작업량
1주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] 이야기 저장 기능 구현
- [ ] 즐겨찾기 기능 구현
- [ ] 공유 링크 생성 기능 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)" \\
  --label "backlog,enhancement,priority:medium"
EOF

echo ""
echo "=== 낮은 우선순위 (Low Priority) Issues ==="

# B-009: 다국어 지원
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-009: 다국어 지원" \\
  --body "## 📋 기능 설명
한국어, 영어 외 다른 언어 지원

## 🎯 목표
- i18n 프레임워크 적용
- 다국어 번역 시스템 구축
- 언어 선택 UI 구현

## 📊 우선순위
- [x] 🟢 낮음 (Low)

## 📅 예상 작업량
2주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] i18n 프레임워크 적용
- [ ] 최소 3개 언어 지원
- [ ] 언어 선택 UI 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Future" \\
  --label "backlog,enhancement,priority:low"
EOF

echo ""

# B-010: 부모 모니터링 기능
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-010: 부모 모니터링 기능" \\
  --body "## 📋 기능 설명
부모가 아이 활동 모니터링 가능

## 🎯 목표
- 활동 요약 알림
- 주간/월간 리포트
- 읽기 습관 추적

## 📊 우선순위
- [x] 🟢 낮음 (Low)

## 📅 예상 작업량
2주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] 활동 요약 대시보드 구현
- [ ] 알림 시스템 구현
- [ ] 리포트 생성 기능 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 3" \\
  --label "backlog,enhancement,priority:low"
EOF

echo ""

# B-011: 오프라인 모드
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-011: 오프라인 모드" \\
  --body "## 📋 기능 설명
인터넷 없이 기본 기능 사용 가능

## 🎯 목표
- 오프라인 캐싱 시스템
- 저장된 이야기 오프라인 접근
- 동기화 기능

## 📊 우선순위
- [x] 🟢 낮음 (Low)

## 📅 예상 작업량
3주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] Service Worker 구현
- [ ] 오프라인 캐싱 기능 구현
- [ ] 온라인 복귀 시 동기화 기능 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Future" \\
  --label "backlog,enhancement,priority:low"
EOF

echo ""

# B-012: 게이미피케이션
cat << EOF
gh issue create \\
  --title "[BACKLOG] B-012: 게이미피케이션" \\
  --body "## 📋 기능 설명
읽기 목표 달성 시 배지, 보상 시스템

## 🎯 목표
- 읽기 목표 설정 기능
- 배지 시스템
- 보상 시스템

## 📊 우선순위
- [x] 🟢 낮음 (Low)

## 📅 예상 작업량
2주

## ✅ 완료 조건 (Acceptance Criteria)
- [ ] 목표 설정 UI 구현
- [ ] 배지 시스템 구현
- [ ] 보상 시스템 구현
- [ ] 테스트 완료

## 📝 관련 문서
- [BACKLOG.md](${REPO_URL}/blob/main/BACKLOG.md)
- [ROADMAP.md](${REPO_URL}/blob/main/ROADMAP.md) - Phase 4" \\
  --label "backlog,enhancement,priority:low"
EOF

echo ""
echo "=== 완료 ==="
echo ""
echo "위 명령어들을 순서대로 실행하면 12개의 백로그 Issues가 생성됩니다."
echo ""
echo "생성 후 GitHub Projects에서 Issues를 프로젝트 보드에 추가하세요:"
echo "1. ${REPO_URL}/issues 로 이동"
echo "2. 각 Issue 페이지에서 'Projects' 섹션 클릭"
echo "3. 프로젝트 선택"
echo ""
echo "또는 GitHub Projects 페이지에서 '+ Add items' 버튼으로 Issues를 추가할 수 있습니다."
echo ""
echo "📋 Projects 보드: https://github.com/users/deokhwajeong/projects/7/views/2"
