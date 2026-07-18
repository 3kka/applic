#!/usr/bin/env python3
"""
convert.py — Dynamic Suffix-Based Schedule Compiler (with Dynamic Titles)
"""

import os
import sys
import json
import pandas as pd

RAW_DATA = os.environ.get('RAW_DATA')
OUTPUT_FILE = 'data.json'

def build_iso(date_val: str, iso_val: str) -> list:
    if iso_val:
        parts = [d.strip() for d in iso_val.split(';') if d.strip()]
        if parts:
            return parts
    if date_val:
        return [date_val]
    return []

def main():
    if not RAW_DATA:
        print('ERROR: RAW_DATA environment variable is not set.', file=sys.stderr)
        sys.exit(1)

    try:
        data_matrix = json.loads(RAW_DATA)
        
        # Row 1 (index 0) = Titles, Row 2 (index 1) = Headers, Row 3+ = Data
        if not data_matrix or len(data_matrix) < 3:
            print('ERROR: Sheet data is empty or missing data rows.', file=sys.stderr)
            sys.exit(1)
            
        title_row = data_matrix[0]
        headers = data_matrix[1]
        rows = data_matrix[2:]
        df = pd.DataFrame(rows, columns=headers)
        
    except Exception as e:
        print(f'ERROR: Failed to parse RAW_DATA JSON: {e}', file=sys.stderr)
        sys.exit(1)

    # Clean all cell values immediately
    df = df.astype(str).apply(lambda col: col.str.strip())
    df = df.fillna('')

    final_json_structure = {}

    # ── DYNAMIC SUFFIX DETECTION ─────────────────────────────────────────────
    sections = set()
    for col in df.columns:
        if " - " in str(col):
            sections.add(str(col).split(" - ", 1)[1].strip())

    # ── PROCESS EACH SECTION & EXTRACT TITLE ─────────────────────────────────
    for section in sections:
        event_col = f"Event - {section}"
        date_col = f"Date - {section}"
        iso_col = f"ISO - {section}"

        if event_col in df.columns and date_col in df.columns:
            
            # 1. Dynamically find the Row 1 Title for this section
            page_title = f"{section} Schedule" # Safe fallback
            try:
                # Find exactly where the Event column sits in Row 2
                col_idx = headers.index(event_col)
                
                # Scan backwards in Row 1 to find the merged title text
                for k in range(col_idx, -1, -1):
                    if k < len(title_row) and str(title_row[k]).strip():
                        page_title = str(title_row[k]).strip()
                        break
            except ValueError:
                pass # Use fallback if indexing fails
            
            # 2. Extract the row records
            section_records = []
            for _, row in df.iterrows():
                event_val = row.get(event_col, '').strip()
                date_val = row.get(date_col, '').strip()
                iso_val = row.get(iso_col, '').strip() if iso_col in df.columns else ''

                if not event_val:
                    continue

                section_records.append({
                    'event': event_val,
                    'date': date_val,
                    'iso': build_iso(date_val, iso_val)
                })
            
            # 3. Build the final nested object
            if section_records:
                final_json_structure[section] = {
                    "pageTitle": page_title,
                    "records": section_records
                }

    # ── WRITE OUTPUT ─────────────────────────────────────────────────────────
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_json_structure, f, ensure_ascii=False, indent=2)

    print(f'SUCCESS: Data exported → {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
