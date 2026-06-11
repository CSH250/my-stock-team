# my-stock-team

종목 이름만 말하면 **여러 애널리스트 AI가 협업해 재무·주가·뉴스·리스크를 분석하고, 그 결과를 PPTX/PDF 리포트로 만들어주는** Claude Code 플러그인입니다.

> ⚠️ 실습/학습용입니다. 투자 권유가 아니며, 최종 판단은 사람이 합니다.

## 설치

Claude Code 안에서 아래 두 줄을 입력하세요:

```
/plugin marketplace add CSH250/my-stock-team
/plugin install my-stock-team@my-stock-team
```

## 사용법

설치 후, Claude Code에 그냥 말하면 됩니다:

```
삼성전자 분석해줘
```

그러면 팀이 순서대로 일합니다:
1. **펀더멘털·기술·뉴스 애널리스트**가 동시에 분석 (재무·주가추세·뉴스심리)
2. **리스크 매니저**가 종합해 핵심 리스크 정리
3. 결과를 `reports/삼성전자.md` 로 저장

이어서 리포트가 필요하면:

```
삼성전자 리포트 PPTX로 만들어줘
```

→ `reports/삼성전자.pptx` 와 `reports/삼성전자.pdf` 생성 (표지·재무표·주가차트·뉴스·리스크·종합·출처 8면).

명령어로 직접 부를 수도 있습니다:

```
/my-stock-team:analyze 삼성전자 005930
/my-stock-team:report  reports/삼성전자.md --ticker 005930
```

## ⚠️ DART API 키는 각자 발급해서 넣으세요

재무·공시 분석은 금융감독원 **DART**의 무료 공개 API를 씁니다. **키는 이 플러그인에 포함돼 있지 않으니** 각자 발급해야 합니다.

1. https://opendart.fss.or.kr 가입 → **인증키 신청** (무료, 즉시 발급)
2. 작업하는 프로젝트 폴더의 `.env` 파일에 한 줄 추가:
   ```
   DART_KEY=발급받은_키
   ```
   (`.env` 는 비밀 파일이라 GitHub 등에 올리면 안 됩니다.)

주가·뉴스·리스크 분석(FinanceDataReader·웹서치·pykrx)은 키가 필요 없습니다.

## 필요한 파이썬 패키지

리포트 생성 시 한 번만 설치하면 됩니다:

```
pip install python-pptx reportlab matplotlib finance-datareader pykrx requests
```

## 구성

| 폴더 | 내용 |
|------|------|
| `agents/` | 애널리스트 서브에이전트 4종 (펀더멘털·기술·뉴스심리·리스크) |
| `skills/report-pptx/` | 리서치 `.md` → PPTX/PDF 변환 (KB 톤·맑은 고딕) |
| `commands/` | `analyze`(풀 리서치)·`report`(리포트 생성) 실행 커맨드 |

## 지켜지는 원칙 (가드레일)

- 모든 수치에 `(출처: 데이터명, 연도/날짜)` — 출처 없는 수치는 싣지 않음
- 못 구한 값은 "확인 불가", 루머는 "미확인"
- 매수/매도·목표가 단정 금지 — 판단 근거 정리까지만, 최종 판단은 사람
