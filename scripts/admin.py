#!/usr/bin/env python3
"""관리자용: 기록 삭제.  python admin.py delete_entry <case> <user> | reset_case <case>"""
import json
import os
import sys
from pathlib import Path

BOARD = Path(os.environ.get("BOARD", Path(__file__).resolve().parent.parent / "docs" / "leaderboard.json"))


def main():
    action, case_id = sys.argv[1], sys.argv[2]
    user = sys.argv[3].strip().lstrip("@") if len(sys.argv) > 3 else ""
    board = json.loads(BOARD.read_text(encoding="utf-8"))
    entries = board["cases"].setdefault(case_id, {})
    if action == "reset_case":
        n = len(entries)
        board["cases"][case_id] = {}
        print(f"Case {case_id}: {n}건 삭제")
    elif action == "delete_entry":
        if user not in entries:
            sys.exit(f"Case {case_id}에 '{user}' 기록이 없습니다.")
        del entries[user]
        print(f"Case {case_id}: {user} 기록 삭제")
    else:
        sys.exit("알 수 없는 action")
    BOARD.write_text(json.dumps(board, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
