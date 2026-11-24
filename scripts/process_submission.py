#!/usr/bin/env python3
"""이슈 제출 1건을 채점하고 docs/leaderboard.json 을 갱신한다."""
import json
import os
import re
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from evaluate import evaluate, load_json

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = Path(os.environ.get("CASES_DIR", ROOT / "cases"))
BOARD = Path(os.environ.get("BOARD", ROOT / "docs" / "leaderboard.json"))
COMMENT = Path(os.environ.get("COMMENT_PATH", "/tmp/comment.md"))
KST = timezone(timedelta(hours=9))


def parse_sections(body):
    parts = re.split(r"^###\s+(.+?)\s*$", body.replace("\r\n", "\n"), flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def clean_csv(text):
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\s*\n", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip() + "\n"


def reply(lines):
    COMMENT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    body = os.environ.get("ISSUE_BODY", "")
    user = os.environ["ISSUE_USER"]
    sec = parse_sections(body)
    m = re.search(r"[1-5]", sec.get("Case", ""))
    if not m:
        return reply(["❌ Case를 읽지 못했습니다. 제출 양식을 그대로 사용해 주세요."])
    case_id = m.group(0)
    case_path = CASES_DIR / f"case{case_id}.json"
    if not case_path.exists():
        return reply([f"❌ Case {case_id}의 문제 파일이 저장소에 없습니다. 관리자에게 문의하세요."])
    csv_text = clean_csv(sec.get("제출 CSV", ""))

    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, encoding="utf-8", newline="") as tmp:
        tmp.write(csv_text)
        tmp_path = tmp.name
    try:
        result = evaluate(load_json(case_path), tmp_path)
    except ValueError as exc:
        return reply([f"❌ **Case {case_id} 제출 실패**", "", f"CSV 형식 오류: {exc}"])
    finally:
        os.unlink(tmp_path)

    if result["errors"]:
        return reply([f"❌ **Case {case_id} 제출 실패 — 제약조건 위반**", ""] +
                     [f"- {e}" for e in result["errors"]] +
                     ["", f"(참고) 계산된 목적함수값: {result['objective']:,.4f}"])

    obj = round(result["objective"], 6)
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    entries = board["cases"].setdefault(case_id, {})
    old = entries.get(user)
    if old and old["objective"] <= obj + 1e-9:
        return reply([f"✅ 검증은 통과했지만 기존 기록({old['objective']:,.4f})이 더 좋거나 같아 갱신하지 않았습니다.",
                      f"이번 제출 Z = {obj:,.4f}"])
    layout = [line.strip() for line in csv_text.splitlines()[1:] if line.strip()]
    entries[user] = {
        "objective": obj,
        "time": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
        "issue": os.environ.get("ISSUE_NUMBER", ""),
        "layout": layout,
    }
    BOARD.write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")
    ranked = sorted(entries.items(), key=lambda kv: (kv[1]["objective"], kv[1]["time"]))
    rank = [n for n, _ in ranked].index(user) + 1
    reply([f"✅ **Case {case_id} 등록 완료**", "",
           f"- 참가자: @{user}", f"- 목적함수값 Z = **{obj:,.4f}**",
           f"- 현재 순위: **{rank}위 / {len(ranked)}명**"])


if __name__ == "__main__":
    main()
