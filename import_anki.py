#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anki .apkg 파일을 memory-cards 웹앱 데이터로 변환하는 스크립트.
- 900장의 Speaking Matrix 카드 추출 -> cards-data.json
- 1,592건의 Anki 복습 로그(revlog) 추출 -> cards-log-YYYY-Www.json
- 최신 학습 상태 동기화
"""

import zipfile
import io
import sqlite3
import os
import json
import datetime
import html
import sys
import zstandard

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

KST = datetime.timezone(datetime.timedelta(hours=9))

def js_week_key(ts_ms):
    dt_kst = datetime.datetime.fromtimestamp(ts_ms / 1000.0, tz=KST)
    t = dt_kst - datetime.timedelta(hours=4)
    iso = t.date().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

def extract_anki_db(apkg_path):
    with zipfile.ZipFile(apkg_path, 'r') as z:
        if 'collection.anki21b' in z.namelist():
            compressed = z.read('collection.anki21b')
            dctx = zstandard.ZstdDecompressor()
            with dctx.stream_reader(io.BytesIO(compressed)) as reader:
                decompressed = reader.read()
            temp_db = 'temp_collection.anki21'
            with open(temp_db, 'wb') as f:
                f.write(decompressed)
            return temp_db
        elif 'collection.anki2' in z.namelist():
            z.extract('collection.anki2', '.')
            return 'collection.anki2'
        else:
            raise FileNotFoundError("Anki collection database not found in package.")

def convert_anki_package(apkg_path):
    print(f"[*] Anki 파일 처리 시작: {apkg_path}")
    db_path = extract_anki_db(apkg_path)
    
    conn = sqlite3.connect(db_path)
    conn.create_collation('unicase', lambda a, b: (a > b) - (a < b))
    cur = conn.cursor()

    # 1. 덱 정보 매핑
    cur.execute("SELECT id, name FROM decks;")
    deck_rows = cur.fetchall()
    deck_map = {}
    for did, name in deck_rows:
        deck_map[did] = name.split('\x1f')

    # 2. 카드 및 노트 추출
    cur.execute("""
        SELECT c.id, c.did, n.flds, n.tags, c.queue, c.due, c.ivl, c.reps, c.lapses
        FROM cards c
        JOIN notes n ON c.nid = n.id
        ORDER BY c.id;
    """)
    card_rows = cur.fetchall()
    print(f"[*] 총 {len(card_rows)}장의 카드를 발견했습니다.")

    converted_cards = []
    card_id_map = {} # anki_cid -> new_id

    for row in card_rows:
        cid, did, flds_raw, tags_raw, queue, due, ivl, reps, lapses = row
        flds = flds_raw.split('\x1f')
        
        # 필드 파싱 (Speaking Matrix 구조: SentenceID, Korean, English, Chunk, Situation, Source)
        sentence_id = flds[0].strip() if len(flds) > 0 else f"c_{cid}"
        korean = html.unescape(flds[1].strip() if len(flds) > 1 else "")
        english = html.unescape(flds[2].strip() if len(flds) > 2 else "")
        chunk = html.unescape(flds[3].strip() if len(flds) > 3 else "")
        situation = html.unescape(flds[4].strip() if len(flds) > 4 else "")
        source = html.unescape(flds[5].strip() if len(flds) > 5 else "")

        # 덱 구조 분석 (Speaking Matrix / Unit 01 (Day 01-05) / Day 01 / Input)
        deck_parts = deck_map.get(did, ["기본"])
        unit_name = "Speaking Matrix"
        day_name = ""
        io_type = "문장"

        if len(deck_parts) >= 2:
            unit_name = deck_parts[1] # e.g. "Unit 01 (Day 01-05)"
        if len(deck_parts) >= 3:
            day_name = deck_parts[2]  # e.g. "Day 01"
        if len(deck_parts) >= 4:
            io_type = deck_parts[3]   # e.g. "Input" or "Output"

        # 카드 ID
        card_id = f"sm_{cid}"
        card_id_map[cid] = card_id

        # 앞면 질문 (상단 스코프에 Day와 타입 노출)
        scope_prefix = f"〔{day_name} · {io_type}〕 " if day_name else ""
        front_text = f"{scope_prefix}{korean}"

        # 보충 설명 구성
        notes_lines = []
        if chunk:
            notes_lines.append(f"청크: {chunk}")
        if situation:
            notes_lines.append(f"상황: {situation}")
        note_text = "\n".join(notes_lines)

        tags = [t.strip() for t in tags_raw.split() if t.strip()]
        if day_name and day_name not in tags:
            tags.insert(0, day_name)
        if io_type and io_type not in tags:
            tags.insert(1, io_type)
        if unit_name.split()[0] not in tags:
            tags.append(unit_name.split()[0])

        node_path = f"Speaking Matrix/{unit_name}/{day_name}/{io_type}".replace('//', '/')

        converted_card = {
            "id": card_id,
            "subj": unit_name,
            "typ": io_type,
            "front": front_text,
            "back": english,
            "note": note_text,
            "src": source,
            "tags": tags,
            "node": node_path,
            "items": []
        }
        converted_cards.append(converted_card)

    # 3. cards-data.json 저장
    cards_data = {
        "v": 2,
        "cards": converted_cards
    }
    with open("cards-data.json", "w", encoding="utf-8") as f:
        json.dump(cards_data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 'cards-data.json'에 {len(converted_cards)}장 저장 완료.")

    # 4. revlog (학습 복습 기록) 추출 및 변환
    cur.execute("SELECT id, cid, ease, time FROM revlog ORDER BY id;")
    revlogs = cur.fetchall()
    print(f"[*] 총 {len(revlogs)}건의 복습 기록을 발견했습니다.")

    logs_by_week = {}
    for r in revlogs:
        rid, rcid, ease, time_ms = r
        if rcid not in card_id_map:
            continue
        new_cid = card_id_map[rcid]
        ts_sec = int(rid / 1000)
        wk = js_week_key(rid)
        
        # 웹앱 로그 포맷: [cardId, ts_sec, ease(1-4), {ms: time_ms}]
        log_entry = [new_cid, ts_sec, ease, {"ms": time_ms}]
        if wk not in logs_by_week:
            logs_by_week[wk] = []
        logs_by_week[wk].append(log_entry)

    # 주차별 로그 파일 저장
    for wk, week_logs in logs_by_week.items():
        log_file = f"cards-log-{wk}.json"
        log_content = {
            "v": 2,
            "week": wk,
            "log": week_logs
        }
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_content, f, ensure_ascii=False, indent=2)
        print(f"[OK] 복습 이력 '{log_file}'에 {len(week_logs)}건 기록 완료.")

    # 5. 기본 세션 파일 (cards-sessions.json) 생성
    sessions_file = "cards-sessions.json"
    sessions_content = {
        "v": 1,
        "sessions": [
            {
                "id": "s_default_speaking",
                "name": "Speaking Matrix 데일리",
                "how": {
                    "status": ["due", "new"],
                    "order": "shuffle",
                    "weights": {},
                    "limit": None,
                    "bury": True,
                    "newAfter": True
                },
                "scope": {"units": [], "mids": [], "subj": [], "tags": [], "typ": []},
                "mode": "auto",
                "day": "",
                "q": [],
                "done": 0,
                "scores": []
            }
        ],
        "hoedok": {},
        "read": {},
        "fc": {},
        "cap": 130,
        "capAt": 0,
        "ret": 0.9,
        "retAt": 0,
        "rest": {"dow": 0, "days": [], "skip": []},
        "restAt": 0
    }
    with open(sessions_file, "w", encoding="utf-8") as f:
        json.dump(sessions_content, f, ensure_ascii=False, indent=2)
    print(f"[OK] '{sessions_file}' 기본 세션 설정 완료.")

    # 6. cards-marks.json 초기화
    with open("cards-marks.json", "w", encoding="utf-8") as f:
        json.dump({"v": 1, "cards": {}}, f, ensure_ascii=False, indent=2)

    conn.close()
    if os.path.exists(db_path):
        os.remove(db_path)
    print("\n[COMPLETE] 모든 변환 및 복습 이력 복원이 완료되었습니다!")

if __name__ == '__main__':
    apkg_file = sys.argv[1] if len(sys.argv) > 1 else "Speaking Matrix.apkg"
    if os.path.exists(apkg_file):
        convert_anki_package(apkg_file)
    else:
        print(f"오류: '{apkg_file}' 파일을 찾을 수 없습니다.")
