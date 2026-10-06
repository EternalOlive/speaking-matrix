#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Cards - 내 카드 덱을 cards-data.json으로 변환하는 도구

지원 형식:
1. CSV / TSV 파일:
   - 헤더(선택): subj, front, back, tags, typ, items
   - 또는 단순 2열(질문, 정답) / 3열(과목, 질문, 정답) 등 자동 인식
2. TXT 파일:
   - 질문::정답 형식
   - 또는 Q: 질문 / A: 정답 구분 형식
3. JSON 파일:
   - [{'front': '...', 'back': '...'}, ...] 형태

사용법:
  python build_cards.py sample_cards.csv
  python build_cards.py my_notes.txt
  python build_cards.py --help
"""

import sys
import os
import csv
import json
import hashlib

def generate_card_id(front, back, index):
    raw = f"{index}_{front}_{back}"
    return "c_" + hashlib.md5(raw.encode('utf-8')).hexdigest()[:12]

def parse_csv_or_tsv(filepath):
    delimiter = '\t' if filepath.lower().endswith(('.tsv', '.tab')) else ','
    cards = []
    
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        # 구분자 자동 추정
        sample = f.read(4096)
        f.seek(0)
        if '\t' in sample and delimiter != '\t':
            delimiter = '\t'
            
        reader = csv.reader(f, delimiter=delimiter)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
        
    if not rows:
        return []

    # 헤더 판별
    first_row = [c.strip().lower() for c in rows[0]]
    has_header = False
    col_map = {}
    
    known_fields = {
        'front': ['front', '문제', '질문', 'q', 'question', '앞면', '단어'],
        'back': ['back', '정답', '답', '해설', 'a', 'answer', '뒷면', '뜻', '의미'],
        'subj': ['subj', 'subject', '과목', '카테고리', '분류', 'category'],
        'tags': ['tags', 'tag', '태그'],
        'typ': ['typ', 'type', '유형', '종류'],
        'items': ['items', 'item', '항목', '상세']
    }
    
    for idx, col in enumerate(first_row):
        for field, aliases in known_fields.items():
            if col in aliases:
                col_map[field] = idx
                has_header = True
                break

    data_rows = rows[1:] if has_header else rows
    
    for i, row in enumerate(data_rows, 1):
        if not any(cell.strip() for cell in row):
            continue
            
        card = {}
        if has_header and 'front' in col_map and 'back' in col_map:
            front = row[col_map['front']].strip() if col_map['front'] < len(row) else ''
            back = row[col_map['back']].strip() if col_map['back'] < len(row) else ''
            subj = row[col_map['subj']].strip() if 'subj' in col_map and col_map['subj'] < len(row) else '기본'
            tags_raw = row[col_map['tags']].strip() if 'tags' in col_map and col_map['tags'] < len(row) else ''
            typ = row[col_map['typ']].strip() if 'typ' in col_map and col_map['typ'] < len(row) else ''
            items_raw = row[col_map['items']].strip() if 'items' in col_map and col_map['items'] < len(row) else ''
        else:
            # 헤더가 없을 때 열 개수에 따른 기본 매핑
            if len(row) == 1:
                front = row[0].strip()
                back = ""
                subj = "기본"
                tags_raw, typ, items_raw = "", "", ""
            elif len(row) == 2:
                # 앞면, 뒷면
                front = row[0].strip()
                back = row[1].strip()
                subj = "기본"
                tags_raw, typ, items_raw = "", "", ""
            elif len(row) == 3:
                # 과목, 앞면, 뒷면
                subj = row[0].strip() or "기본"
                front = row[1].strip()
                back = row[2].strip()
                tags_raw, typ, items_raw = "", "", ""
            else:
                # 과목, 앞면, 뒷면, 태그, ...
                subj = row[0].strip() or "기본"
                front = row[1].strip()
                back = row[2].strip()
                tags_raw = row[3].strip() if len(row) > 3 else ""
                typ = row[4].strip() if len(row) > 4 else ""
                items_raw = row[5].strip() if len(row) > 5 else ""

        if not front and not back:
            continue
            
        tags = [t.strip() for t in tags_raw.replace(';', ',').split(',') if t.strip()] if tags_raw else []
        items = [it.strip() for it in items_raw.replace(';', '\n').split('\n') if it.strip()] if items_raw else []
        
        card = {
            "id": generate_card_id(front, back, i),
            "subj": subj or "기본",
            "typ": typ or "개념",
            "front": front,
            "back": back,
            "tags": tags,
            "items": items
        }
        cards.append(card)
        
    return cards

def parse_txt(filepath):
    cards = []
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        text = f.read()

    # 1. '::' 구분 방식 지원
    lines = text.splitlines()
    has_double_colon = any('::' in l for l in lines)
    if has_double_colon:
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '::' in line:
                parts = line.split('::')
                front = parts[0].strip()
                back = parts[1].strip()
                subj = parts[2].strip() if len(parts) > 2 else "기본"
                cards.append({
                    "id": generate_card_id(front, back, i),
                    "subj": subj,
                    "typ": "개념",
                    "front": front,
                    "back": back,
                    "tags": [],
                    "items": []
                })
        return cards

    # 2. Q: / A: 블록 방식 지원
    blocks = text.split('---') if '---' in text else [text]
    idx = 1
    for block in blocks:
        cur_q = ""
        cur_a = ""
        cur_subj = "기본"
        for line in block.splitlines():
            line_str = line.strip()
            if line_str.startswith(('Q:', 'q:', '문제:')):
                cur_q = line_str.split(':', 1)[1].strip()
            elif line_str.startswith(('A:', 'a:', '정답:', '답:')):
                cur_a = line_str.split(':', 1)[1].strip()
            elif line_str.startswith(('과목:', '분류:')):
                cur_subj = line_str.split(':', 1)[1].strip()
            elif cur_a and line_str:
                cur_a += "\n" + line_str
            elif cur_q and not cur_a and line_str:
                cur_q += "\n" + line_str
                
        if cur_q or cur_a:
            cards.append({
                "id": generate_card_id(cur_q, cur_a, idx),
                "subj": cur_subj or "기본",
                "typ": "개념",
                "front": cur_q,
                "back": cur_a,
                "tags": [],
                "items": []
            })
            idx += 1

    return cards

def parse_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    raw_list = data if isinstance(data, list) else data.get('cards', [])
    cards = []
    for i, item in enumerate(raw_list, 1):
        front = item.get('front', item.get('q', ''))
        back = item.get('back', item.get('a', ''))
        subj = item.get('subj', item.get('subject', '기본'))
        tags = item.get('tags', [])
        typ = item.get('typ', '개념')
        items = item.get('items', [])
        card_id = item.get('id') or generate_card_id(front, back, i)
        cards.append({
            "id": card_id,
            "subj": subj,
            "typ": typ,
            "front": front,
            "back": back,
            "tags": tags if isinstance(tags, list) else [tags],
            "items": items if isinstance(items, list) else [items]
        })
    return cards

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print("사용법: python build_cards.py <입력파일> [출력파일]")
        print("예시: python build_cards.py my_cards.csv")
        print("      python build_cards.py my_notes.txt")
        print("기본 출력 파일은 'cards-data.json' 입니다.")
        sys.exit(0)

    src_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else "cards-data.json"

    if not os.path.exists(src_file):
        print(f"오류: 입력 파일 '{src_file}'을 찾을 수 없습니다.")
        sys.exit(1)

    ext = os.path.splitext(src_file)[1].lower()
    if ext in ('.csv', '.tsv', '.tab'):
        cards = parse_csv_or_tsv(src_file)
    elif ext in ('.txt', '.md'):
        cards = parse_txt(src_file)
    elif ext == '.json':
        cards = parse_json(src_file)
    else:
        print(f"알 수 없는 파일 확장자 '{ext}'. CSV 또는 TXT 파서로 시도합니다.")
        cards = parse_csv_or_tsv(src_file) or parse_txt(src_file)

    if not cards:
        print("카드를 추출하지 못했습니다. 파일 내용을 확인해 주세요.")
        sys.exit(1)

    result = {
        "v": 2,
        "cards": cards
    }

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n성공! 총 {len(cards)}장의 카드가 '{out_file}'에 저장되었습니다.")
    
    # 과목별 장수 집계
    by_subj = {}
    for c in cards:
        s = c.get('subj', '기본')
        by_subj[s] = by_subj.get(s, 0) + 1
    print("과목별 집계:")
    for s, n in sorted(by_subj.items()):
        print(f"  - {s}: {n}장")

if __name__ == '__main__':
    main()
