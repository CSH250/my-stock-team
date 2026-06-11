---
description: reports/{종목}.md 를 디자인된 PPTX·PDF 리포트로 변환한다 (KB 톤·맑은 고딕·8슬라이드)
argument-hint: <reports/종목.md 경로> [--ticker 6자리코드]
allowed-tools: Bash
---

입력 마크다운: `$ARGUMENTS` (예: `reports/삼성전자.md --ticker 005930`).

`report-pptx` 스킬의 빌더로 PPTX 와 PDF 를 둘 다 생성하라. 플러그인 내장 스크립트를 `${CLAUDE_PLUGIN_ROOT}` 로 참조한다 (한글 깨짐 방지로 `PYTHONUTF8=1`):

```bash
PYTHONUTF8=1 python "${CLAUDE_PLUGIN_ROOT}/skills/report-pptx/build_pptx.py" $ARGUMENTS
PYTHONUTF8=1 python "${CLAUDE_PLUGIN_ROOT}/skills/report-pptx/build_pdf.py"  $ARGUMENTS
```

- 두 빌더는 같은 `.md`·같은 디자인을 공유한다(표지→개요→재무표→가격차트→뉴스→리스크→한 줄 종합→데이터 출처, 8면).
- 표지엔 "무료 공개 데이터 기반 학습용" 고지, 마지막엔 출처·기준일 면이 자동 삽입된다.
- 의존성 미설치 시: `pip install python-pptx reportlab matplotlib finance-datareader`.

생성된 파일 경로(`reports/{종목}.pptx`, `reports/{종목}.pdf`)를 사용자에게 알린다.
