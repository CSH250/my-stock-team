# my-stock-team (Claude Code 플러그인)

한국 주식 리서치를 **여러 애널리스트 서브에이전트의 협업**으로 생성하고, 결과를 **디자인된 PPTX/PDF 리포트**로 내보내는 Claude Code 플러그인입니다.

## 구성

```
my-stock-team/
├─ .claude-plugin/
│  ├─ plugin.json        # 플러그인 매니페스트 (name=my-stock-team, v1.0.0)
│  └─ marketplace.json   # 설치 카탈로그
├─ agents/               # 4종 애널리스트 서브에이전트
│  ├─ fundamental-analyst-dart.md   # 재무·공시 (DART OpenAPI)
│  ├─ market-technical-analyst.md   # 주가·추세 (FinanceDataReader)
│  ├─ news-sentiment-analyst.md     # 뉴스·심리 (웹서치)
│  └─ risk-manager-analyst.md       # 리스크·유동성 (pykrx)
├─ skills/
│  └─ report-pptx/       # 리서치 .md → PPTX/PDF (KB 톤·맑은 고딕)
└─ commands/
   ├─ analyze.md         # /my-stock-team:analyze — 종목 1개 풀 리서치
   └─ report.md          # /my-stock-team:report  — .md → PPTX/PDF
```

## 사용법

```
/my-stock-team:analyze 삼성전자 005930      # reports/삼성전자.md 생성
/my-stock-team:report  reports/삼성전자.md --ticker 005930   # PPTX+PDF 생성
```

## 사전 준비

- **DART API 키**: 각자 [opendart.fss.or.kr](https://opendart.fss.or.kr) 에서 무료 발급 후, 작업 프로젝트의 `.env` 에 `DART_KEY=...` 로 넣습니다. **이 플러그인에는 어떤 비밀값도 포함돼 있지 않습니다.**
- **파이썬 패키지**: `pip install python-pptx reportlab matplotlib finance-datareader requests`

## 설치 (마켓플레이스)

```
/plugin marketplace add <이 저장소 경로 또는 깃 URL>
/plugin install my-stock-team@my-stock-team-marketplace
```

## 가드레일 (모든 산출물에 적용)

- 모든 수치에 `(출처: 데이터명, 연도/날짜)` — 출처 없는 수치는 싣지 않음
- 못 구한 값은 "확인 불가", 루머는 "미확인"
- 매수/매도·목표가 단정 금지 — 의사결정 지원까지만, 최종 판단은 사람
- 리포트 첫머리 "무료 공개 데이터 기반 학습용", 끝에 출처·기준일 목록
