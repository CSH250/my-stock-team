"""reports/{종목명}.md 를 읽어 디자인된 PDF 리포트(reports/{종목명}.pdf)를 생성한다.

PPTX 버전과 동일한 사양·디자인(KB 옐로우, 맑은 고딕, 7페이지 고정 순서)을 따른다.
마크다운 파싱·차트 생성 로직은 build_pptx.py 의 함수를 그대로 재사용한다.

사용:
    python .claude/skills/report-pptx/build_pdf.py "reports/삼성전자.md" --ticker 005930
"""

import argparse
import sys
from datetime import date
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# PPTX 빌더의 파싱/차트 헬퍼 재사용 (같은 폴더)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pptx import (  # noqa: E402
    parse_markdown,
    find_section,
    extract_table,
    extract_ticker,
    body_to_bullets,
    _clean_inline,
    _make_price_chart,
)

# ---------------------------------------------------------------------------
# 디자인 상수 (PPTX 와 동일 톤)
# ---------------------------------------------------------------------------
KB_YELLOW = HexColor("#FFBC00")
GRAY_DARK = HexColor("#333333")
GRAY_MID = HexColor("#666666")
GRAY_LIGHT = HexColor("#F2F2F2")
WHITE = HexColor("#FFFFFF")

FONT = "Malgun"        # 맑은 고딕 (일반)
FONT_BD = "MalgunBd"   # 맑은 고딕 (볼드)

PAGE = landscape(A4)           # 가로 방향(슬라이드 느낌)
PW, PH = PAGE                  # 폭/높이 (pt)
MARGIN = 18 * mm
CONTENT_W = PW - MARGIN * 2
MAX_TABLE_ROWS = 9             # 헤더 포함, 넘치면 절단


def _register_fonts():
    fonts = {
        FONT: r"C:\Windows\Fonts\malgun.ttf",
        FONT_BD: r"C:\Windows\Fonts\malgunbd.ttf",
    }
    for name, path in fonts.items():
        if Path(path).exists():
            pdfmetrics.registerFont(TTFont(name, path))
        else:
            # 폰트 없으면 기본 폰트로 대체 (깨질 수 있으나 생성은 계속)
            pdfmetrics.registerFont(TTFont(name, fonts[FONT]))


# ---------------------------------------------------------------------------
# 그리기 헬퍼
# ---------------------------------------------------------------------------
def _wrap(c, text, font, size, max_w):
    """max_w(pt) 안에 들어가도록 텍스트를 줄바꿈한 줄 목록 반환."""
    words = text.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(trial, font, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _header(c, title, kicker):
    """페이지 상단 공통 헤더: 키커 + 제목 + KB 옐로우 강조 바."""
    if kicker:
        c.setFont(FONT_BD, 9)
        c.setFillColor(GRAY_MID)
        c.drawString(MARGIN, PH - MARGIN - 6, kicker)
    c.setFont(FONT_BD, 20)
    c.setFillColor(GRAY_DARK)
    c.drawString(MARGIN, PH - MARGIN - 26, title)
    c.setFillColor(KB_YELLOW)
    c.rect(MARGIN, PH - MARGIN - 36, 34 * mm, 3, fill=1, stroke=0)


def _footer(c, text="투자 판단은 사람 · 본 자료는 정보 제공 목적"):
    c.setFont(FONT, 7.5)
    c.setFillColor(GRAY_MID)
    c.drawString(MARGIN, MARGIN - 6, text)


def _draw_bullets(c, bullets, x, y, width, gap=16, size0=12, size1=10.5):
    """불릿 목록을 (x, y) 상단부터 아래로 그린다. 남은 y 반환."""
    for text, level in bullets:
        size = size0 if level == 0 else size1
        indent = 0 if level == 0 else 14
        mark = "●" if level == 0 else "–"
        # 마커
        c.setFont(FONT_BD if level == 0 else FONT, size)
        c.setFillColor(KB_YELLOW if level == 0 else GRAY_MID)
        c.drawString(x + indent, y, mark)
        # 본문 (줄바꿈)
        text_x = x + indent + 14
        lines = _wrap(c, text, FONT, size, width - indent - 14)
        c.setFont(FONT_BD if level == 0 else FONT, size)
        c.setFillColor(GRAY_DARK)
        for ln in lines:
            c.drawString(text_x, y, ln)
            y -= size + 3
        y -= gap - (size + 3)
        if y < MARGIN + 20:   # 페이지 하단 보호
            break
    return y


# ---------------------------------------------------------------------------
# 페이지 7종
# ---------------------------------------------------------------------------
def page_cover(c, name, report_date):
    # 좌측 KB 옐로우 띠
    c.setFillColor(KB_YELLOW)
    c.rect(0, 0, 10 * mm, PH, fill=1, stroke=0)
    c.setFillColor(GRAY_DARK)
    c.setFont(FONT_BD, 40)
    c.drawString(MARGIN + 6 * mm, PH * 0.58, name)
    c.setFillColor(GRAY_MID)
    c.setFont(FONT, 18)
    c.drawString(MARGIN + 6 * mm, PH * 0.58 - 34, "종목 리서치 리포트")
    # 가드레일 고지: 첫머리 "무료 공개 데이터 기반 학습용"
    c.setFillColor(KB_YELLOW)
    c.setFont(FONT_BD, 13)
    c.drawString(MARGIN + 6 * mm, PH * 0.58 - 60, "무료 공개 데이터 기반 학습용")
    c.setFillColor(GRAY_MID)
    c.setFont(FONT, 12)
    c.drawString(MARGIN + 6 * mm, PH * 0.58 - 84, f"작성일 {report_date}")
    _footer(c, "투자 판단은 사람 · 매수/매도·목표가 의견을 제시하지 않습니다")
    c.showPage()


def page_bullets(c, title, kicker, body, limit=8):
    _header(c, title, kicker)
    bullets = body_to_bullets(body, limit=limit)
    y = PH - MARGIN - 56
    if not bullets:
        c.setFont(FONT, 11)
        c.setFillColor(GRAY_MID)
        c.drawString(MARGIN, y, "내용 없음 (입력 .md 에 해당 섹션이 비어 있음)")
    else:
        _draw_bullets(c, bullets, MARGIN, y, CONTENT_W)
    _footer(c)
    c.showPage()


def page_financials(c, body):
    _header(c, "재무 요약", "FINANCIALS · 최근 3개년")
    y = PH - MARGIN - 56
    table = extract_table(body)
    if table:
        header, data = table
        max_data = MAX_TABLE_ROWS - 1
        trimmed = len(data) > max_data
        data = data[:max_data]
        ncols = len(header)
        col_w = CONTENT_W / ncols
        row_h = 22
        x0 = MARGIN
        # 헤더 행
        c.setFillColor(KB_YELLOW)
        c.rect(x0, y - row_h, CONTENT_W, row_h, fill=1, stroke=0)
        c.setFillColor(GRAY_DARK)
        c.setFont(FONT_BD, 10.5)
        for ci, h in enumerate(header):
            c.drawCentredString(x0 + col_w * ci + col_w / 2, y - row_h + 7,
                                _clean_inline(h))
        y -= row_h
        # 데이터 행 (줄무늬)
        c.setFont(FONT, 10)
        for ri, row in enumerate(data):
            c.setFillColor(GRAY_LIGHT if ri % 2 else WHITE)
            c.rect(x0, y - row_h, CONTENT_W, row_h, fill=1, stroke=0)
            c.setFillColor(GRAY_DARK)
            for ci in range(ncols):
                val = _clean_inline(row[ci]) if ci < len(row) else ""
                if ci == 0:
                    c.drawString(x0 + col_w * ci + 6, y - row_h + 7, val)
                else:
                    c.drawRightString(x0 + col_w * (ci + 1) - 6,
                                      y - row_h + 7, val)
            y -= row_h
        # 표 외곽선
        c.setStrokeColor(GRAY_MID)
        c.setLineWidth(0.4)
        c.rect(x0, y, CONTENT_W, row_h * (len(data) + 1), fill=0, stroke=1)
        y -= 12
        if trimmed:
            c.setFont(FONT, 8)
            c.setFillColor(GRAY_MID)
            c.drawString(MARGIN, y, "※ 표 행이 많아 일부만 표시했습니다.")
            y -= 12
    # 표 아래 코멘트
    bullets = body_to_bullets(body, limit=4)
    if bullets:
        _draw_bullets(c, bullets, MARGIN, y - 8, CONTENT_W, gap=14,
                      size0=10.5, size1=10)
    _footer(c)
    c.showPage()


def page_price(c, body, ticker, report_date, out_dir):
    _header(c, "가격 · 추세", "PRICE & TREND")
    y_top = PH - MARGIN - 56
    chart_path = _make_price_chart(ticker, out_dir, report_date) if ticker else None

    if chart_path and chart_path.exists():
        # 차트 좌측
        img_w = CONTENT_W * 0.56
        img_h = img_w * 0.62
        c.drawImage(str(chart_path), MARGIN, y_top - img_h, width=img_w,
                    height=img_h, preserveAspectRatio=True, anchor="nw")
        try:
            chart_path.unlink()
        except OSError:
            pass
        # 코멘트 우측
        bx = MARGIN + img_w + 12 * mm
        _draw_bullets(c, body_to_bullets(body, limit=6), bx, y_top,
                      PW - bx - MARGIN, gap=14, size0=10.5, size1=10)
    else:
        if ticker:
            c.setFont(FONT, 9)
            c.setFillColor(GRAY_MID)
            c.drawString(MARGIN, y_top, "(차트 생성 실패 — 텍스트 요약으로 대체)")
            y_top -= 16
        _draw_bullets(c, body_to_bullets(body, limit=8), MARGIN, y_top, CONTENT_W)
    _footer(c)
    c.showPage()


def page_oneline(c, body):
    _header(c, "한 줄 종합", "SUMMARY")
    # 강조 박스
    box_y, box_h = PH * 0.30, PH * 0.34
    c.setFillColor(GRAY_LIGHT)
    c.setStrokeColor(KB_YELLOW)
    c.setLineWidth(2)
    c.rect(MARGIN, box_y, CONTENT_W, box_h, fill=1, stroke=1)
    bullets = body_to_bullets(body, limit=3)
    y = box_y + box_h - 30
    if bullets:
        for i, (text, level) in enumerate(bullets):
            size = 15 if i == 0 else 13
            c.setFont(FONT_BD if i == 0 else FONT, size)
            c.setFillColor(GRAY_DARK)
            for ln in _wrap(c, text, FONT_BD if i == 0 else FONT, size,
                            CONTENT_W - 30 * mm):
                c.drawString(MARGIN + 14 * mm, y, ln)
                y -= size + 5
            y -= 8
    else:
        c.setFont(FONT, 15)
        c.setFillColor(GRAY_MID)
        c.drawString(MARGIN + 14 * mm, y, "종합 의견 없음")
    _footer(c, "투자 판단은 사람 · 매수/매도·목표가 의견을 제시하지 않습니다")
    c.showPage()


def page_sources(c, body):
    """가드레일: 리포트 끝에 데이터 출처·기준일 목록."""
    _header(c, "데이터 출처 · 기준일", "SOURCES")
    y = PH - MARGIN - 56
    bullets = body_to_bullets(body, limit=12)
    if bullets:
        _draw_bullets(c, bullets, MARGIN, y, CONTENT_W, gap=14,
                      size0=11, size1=10)
    else:
        c.setFont(FONT, 11)
        c.setFillColor(GRAY_MID)
        c.drawString(MARGIN, y,
                     "출처 목록이 입력 .md 에 없습니다 (가드레일: 출처·기준일 목록 필수).")
    _footer(c, "무료 공개 데이터 기반 학습용 · 투자 판단은 사람")
    c.showPage()


# ---------------------------------------------------------------------------
# 메인
# ---------------------------------------------------------------------------
def build(md_path: Path, ticker: str | None = None) -> Path:
    _register_fonts()
    md_text = md_path.read_text(encoding="utf-8")
    parsed = parse_markdown(md_text)
    name = md_path.stem
    report_date = parsed["_date"]
    sections = parsed["sections"]
    ticker = ticker or extract_ticker(md_text)
    out_dir = md_path.parent
    out_path = out_dir / f"{name}.pdf"

    c = canvas.Canvas(str(out_path), pagesize=PAGE)
    c.setTitle(f"{name} 종목 리서치 리포트")

    page_cover(c, name, report_date)
    page_bullets(c, "종목 개요", "OVERVIEW",
                 find_section(sections, ["개요", "Overview", "소개"]))
    page_financials(c, find_section(sections, ["재무", "Financial", "실적"]))
    page_price(c, find_section(sections, ["가격", "추세", "기술", "Price"]),
               ticker, report_date, out_dir)
    page_bullets(c, "뉴스 · 심리", "NEWS & SENTIMENT",
                 find_section(sections, ["뉴스", "심리", "Sentiment", "이슈"]))
    page_bullets(c, "리스크", "RISK",
                 find_section(sections, ["리스크", "Risk", "위험"]))
    page_oneline(c, find_section(sections, ["한 줄", "종합", "결론", "Summary"]))
    page_sources(c, find_section(sections, ["출처", "Source", "데이터 출처"]))

    c.save()
    return out_path


def main():
    ap = argparse.ArgumentParser(description="종목 리서치 .md → 디자인 PDF")
    ap.add_argument("md", help="입력 마크다운 경로 (reports/{종목명}.md)")
    ap.add_argument("--ticker", help="6자리 종목코드(차트용). 미지정 시 본문에서 탐색.")
    args = ap.parse_args()
    md_path = Path(args.md)
    if not md_path.exists():
        sys.exit(f"입력 파일 없음: {md_path}")
    out = build(md_path, args.ticker)
    print(f"생성 완료: {out}")


if __name__ == "__main__":
    main()
