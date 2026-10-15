#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Speaking Matrix 뉘앙스 노트 자동 정렬 및 관리 스크립트
단일 파일 nuance-notes.md 내 Unit/Day 구조를 파싱하여 지정된 Day의 뉘앙스 내용을 항상 올바른 순서의 위치에 삽입/수정합니다.
"""

import os
import re
import argparse

NOTES_FILE = "nuance-notes.md"

def generate_initial_skeleton():
    lines = [
        "# Speaking Matrix 뉘앙스 노트",
        "",
        "Speaking Matrix 900제 문장의 뉘앙스, 원어민 어감 차이, 실전 활용 팁을 정리한 단일 마스터 노트입니다.",
        ""
    ]
    for u in range(1, 19):
        d_start = (u - 1) * 5 + 1
        d_end = u * 5
        lines.append(f"## Unit {u:02d} (Day {d_start:02d}-{d_end:02d})")
        lines.append("")
        for d in range(d_start, d_end + 1):
            lines.append(f'<div id="day-{d:02d}"></div>')
            lines.append(f"### Day {d:02d}")
            if d == 23:
                lines.append("- **I usually drink tea, but today I went with coffee to focus.**")
                lines.append("  - `went with`: 단순히 `chose`보다 여러 선택지 중 '이걸로 결정했다/택했다'는 자연스러운 구어체 뉘앙스입니다. 식당이나 카페에서 주문할 때도 자주 쓰입니다.")
                lines.append("  - `to focus`: `in order to focus`의 일상적 축약 형태로, 목적을 간결하게 표현합니다.")
                lines.append("  - `usually` vs `normally`: `usually`는 일상적인 빈도/습관에 초점이 있고, `normally`는 일반적인 규칙/상태에 초점이 있습니다.")
            elif d == 1:
                lines.append("- **I just woke up.**")
                lines.append("  - `just`: 직전의 순간을 강조하는 부사로, '방금 막' 일어났음을 나타냅니다.")
                lines.append("  - `wake up` vs `get up`: `wake up`은 눈을 뜬 상태, `get up`은 침대에서 몸을 일으켜 나온 상태를 의미합니다.")
            else:
                lines.append("*등록된 뉘앙스 노트가 없습니다.*")
            lines.append("")
    return "\n".join(lines) + "\n"

def upsert_day_content(filepath, day_num, content, append_mode=False):
    if not os.path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(generate_initial_skeleton())

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    target_day = f"Day {day_num:02d}"
    day_header_pattern = rf'(<div id="day-{day_num:02d}"></div>\s*\n\s*###\s*{re.escape(target_day)}\s*\n)'

    match = re.search(day_header_pattern, text)
    if not match:
        print(f"경고: {target_day} 헤더를 찾을 수 없습니다. 파일을 확인하세요.")
        return False

    header_end = match.end()

    # Find the next header (### or ## or <div id=)
    next_header_pattern = r'(\n<div id="day-\d+"|\n###\s+Day|\n##\s+Unit|\Z)'
    next_match = re.search(next_header_pattern, text[header_end:])
    
    if next_match:
        section_end = header_end + next_match.start()
    else:
        section_end = len(text)

    existing_section = text[header_end:section_end].strip()

    clean_content = content.strip()

    if append_mode and existing_section and existing_section != "*등록된 뉘앙스 노트가 없습니다.*":
        new_section = existing_section + "\n\n" + clean_content
    else:
        new_section = clean_content

    updated_text = text[:header_end] + new_section + "\n\n" + text[section_end:].lstrip("\n")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(updated_text)

    print(f"{target_day} 뉘앙스 노트 업데이트 완료: {filepath}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Speaking Matrix 뉘앙스 노트 자동 정렬 삽입 도구")
    parser.add_argument("--init", action="store_true", help="nuance-notes.md 기본 골격 초기화")
    parser.add_argument("--day", type=int, help="대상 Day 번호 (1-90)")
    parser.add_argument("--content", type=str, help="삽입할 마크다운 내용")
    parser.add_argument("--append", action="store_true", help="기존 내용 뒤에 추가 (기본은 대체)")
    parser.add_argument("--file", type=str, default=NOTES_FILE, help="대상 노트 파일 경로")

    args = parser.parse_args()

    if args.init or not os.path.exists(args.file):
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(generate_initial_skeleton())
        print(f"{args.file} 파일 초기화 완료 (Unit 01-18, Day 01-90 포함).")
        if not args.day:
            return

    if args.day and args.content:
        upsert_day_content(args.file, args.day, args.content, append_mode=args.append)
    elif args.day and not args.content:
        print("내용(--content)을 입력해주세요.")

if __name__ == "__main__":
    main()
