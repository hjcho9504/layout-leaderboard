#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Facility Layout - Objective evaluator (shared by the GitHub Action)
- Select the Case 2 JSON definition and a submitted dept,x,y,rot CSV.
- Calculates sum(flow_ij * ManhattanDistance(center_i, center_j)).
- Checks department count, dimensions/rotation, building bounds, reserve,
  pairwise overlap, dock contact, and wall contact.
- Standard-library only (Python 3.9+).
"""

import csv
import json

EPS = 1e-6


def load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def load_layout_csv(path):
    rows = {}
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"dept", "x", "y", "rot"}
        if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
            raise ValueError("CSV 헤더는 dept,x,y,rot 이어야 합니다.")
        for line_no, row in enumerate(reader, start=2):
            dept = (row.get("dept") or "").strip()
            if not dept:
                raise ValueError(f"{line_no}행: dept 값이 비어 있습니다.")
            if dept in rows:
                raise ValueError(f"{line_no}행: {dept}가 중복 입력되었습니다.")
            try:
                x = float(row["x"])
                y = float(row["y"])
                rot_float = float(row["rot"])
                rot = int(rot_float)
                if abs(rot_float - rot) > EPS:
                    raise ValueError
            except (TypeError, ValueError):
                raise ValueError(f"{line_no}행: x, y는 숫자이고 rot은 0 또는 1이어야 합니다.")
            if rot not in (0, 1):
                raise ValueError(f"{line_no}행: rot은 0 또는 1이어야 합니다.")
            rows[dept] = {"x": x, "y": y, "rot": rot}
    return rows


def evaluate(case, csv_path):
    submitted = load_layout_csv(csv_path)
    shapes = case["shapes"]
    departments = list(case["areas_m2"].keys())

    building = case["building"]
    building_w = float(case.get("meta", {}).get("usable_w", building["w"]))
    building_h = float(case.get("meta", {}).get("usable_h", building["h"]))
    reserve = case.get("reserve", {})
    reserve_x = float(reserve.get("x", building_w))

    errors = []
    warnings = []
    details = []

    missing = sorted(set(departments) - set(submitted))
    extra = sorted(set(submitted) - set(departments))
    if missing:
        errors.append("누락된 부서: " + ", ".join(missing))
    if extra:
        errors.append("JSON에 없는 부서: " + ", ".join(extra))

    rects = {}
    for dept in departments:
        if dept not in submitted:
            continue
        item = submitted[dept]
        rot = item["rot"]
        if dept not in shapes or len(shapes[dept]) <= rot:
            errors.append(f"{dept}: JSON에서 rot={rot}에 해당하는 형상을 찾을 수 없습니다.")
            continue
        w, h = map(float, shapes[dept][rot])
        x, y = item["x"], item["y"]
        rects[dept] = (x, y, w, h, rot)

        if x < -EPS or y < -EPS or x + w > building_w + EPS or y + h > building_h + EPS:
            errors.append(
                f"{dept}: 사용 가능 공간 범위 초과 "
                f"(x={x:g}, y={y:g}, w={w:g}, h={h:g}; "
                f"허용 {building_w:g}×{building_h:g})"
            )

        # Reserve is the right-side strip from reserve.x to building width.
        # For this case it spans the full building height.
        if reserve_x < building["w"] - EPS and x + w > reserve_x + EPS:
            errors.append(f"{dept}: 우측 예비공간(reserve) 침범")

    # Pairwise rectangle overlap check.
    overlap_pairs = []
    rect_names = list(rects)
    for i in range(len(rect_names)):
        a = rect_names[i]
        ax, ay, aw, ah, _ = rects[a]
        for b in rect_names[i + 1:]:
            bx, by, bw, bh, _ = rects[b]
            separated = (
                ax + aw <= bx + EPS or bx + bw <= ax + EPS or
                ay + ah <= by + EPS or by + bh <= ay + EPS
            )
            if not separated:
                overlap_pairs.append((a, b))
    for a, b in overlap_pairs:
        errors.append(f"부서 중첩: {a} / {b}")

    # Dock departments must touch the bottom edge y=0.
    for dept in case.get("dock", []):
        if dept in rects and abs(rects[dept][1]) > EPS:
            errors.append(f"{dept}: 하단 도크(y=0)에 접촉하지 않음")

    # Wall condition: current Case 2 specifies CHRG on x=0.
    wall = case.get("wall", {})
    for dept, condition in wall.items():
        if dept not in rects:
            continue
        text = str(condition).replace(" ", "")
        if "x=0" in text and abs(rects[dept][0]) > EPS:
            errors.append(f"{dept}: 왼쪽 외벽(x=0)에 접촉하지 않음")
        elif "x=0" not in text:
            warnings.append(f"{dept}: 자동 검증하지 못한 외벽 조건: {condition}")

    # Objective: use the original directed flow records. Manhattan distance
    # is symmetric, so opposite-direction flows are both counted as specified.
    flow_total = 0.0
    flow_count = 0
    missing_flow_depts = set()
    for edge, amount in case.get("flow", {}).items():
        if ">" not in edge:
            errors.append(f"잘못된 flow 항목: {edge}")
            continue
        a, b = edge.split(">", 1)
        if a not in rects or b not in rects:
            missing_flow_depts.update([a, b])
            continue
        ax, ay, aw, ah, _ = rects[a]
        bx, by, bw, bh, _ = rects[b]
        center_ax, center_ay = ax + aw / 2, ay + ah / 2
        center_bx, center_by = bx + bw / 2, by + bh / 2
        distance = abs(center_ax - center_bx) + abs(center_ay - center_by)
        contribution = float(amount) * distance
        flow_total += contribution
        flow_count += 1
        details.append((a, b, float(amount), distance, contribution))

    if missing_flow_depts:
        errors.append("물동량 계산에 필요한 부서 좌표 누락: " + ", ".join(sorted(missing_flow_depts)))

    return {
        "objective": flow_total,
        "flow_count": flow_count,
        "flow_sum": sum(float(v) for v in case.get("flow", {}).values()),
        "department_count": len(submitted),
        "expected_count": len(departments),
        "overlap_pairs": overlap_pairs,
        "errors": errors,
        "warnings": warnings,
        "details": details,
        "building_w": building_w,
        "building_h": building_h,
    }
