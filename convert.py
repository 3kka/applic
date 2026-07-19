#!/usr/bin/env python3
"""
convert.py — Fully Dynamic Headless CMS Compiler
"""

import os
import sys
import json
import pandas as pd

RAW_DATA = os.environ.get('RAW_DATA')
OUTPUT_FILE = 'data.json'

def main():
    if not RAW_DATA:
        print('ERROR: RAW_DATA environment variable is not set.', file=sys.stderr)
        sys.exit(1)

    try:
        data_matrix = json.loads(RAW_DATA)
        if not data_matrix or len(data_matrix) < 3:
            print('ERROR: Sheet data is empty or missing rows.', file=sys.stderr)
            sys.exit(1)
            
        title_row = data_matrix[0]
        headers = data_matrix[1]
        rows = data_matrix[2:]
        df = pd.DataFrame(rows, columns=headers)
    except Exception as e:
        print(f'ERROR: Failed to parse JSON: {e}', file=sys.stderr)
        sys.exit(1)

    # Clean all cell values
    df = df.astype(str).apply(lambda col: col.str.strip())
    df = df.fillna('')

    final_json_structure = {}

    # ── 1. DYNAMIC SUFFIX DETECTION ──────────────────────────────────────────
    sections = set()
    for col in df.columns:
        if " - " in str(col):
            sections.add(str(col).split(" - ", 1)[1].strip())

    # ── 2. PROCESS EVERY SECTION AND ITS CUSTOM COLUMNS ──────────────────────
    for section in sections:
        # Find all columns that belong to this specific section suffix
        section_cols = [col for col in df.columns if str(col).endswith(f" - {section}")]
        
        if not section_cols:
            continue

        # Dynamically find the Row 1 Title
        page_title = f"{section} Section"
        try:
            first_col = section_cols[0]
            col_idx = headers.index(first_col)
            for k in range(col_idx, -1, -1):
                if k < len(title_row) and str(title_row[k]).strip():
                    page_title = str(title_row[k]).strip()
                    break
        except ValueError:
            pass

        section_records = []
        for _, row in df.iterrows():
            record = {}
            has_data = False
            
            for col in section_cols:
                # Extract the prefix as the JSON key (e.g., 'news' from 'News - Trending')
                key = str(col).split(" - ", 1)[0].strip().lower()
                val = row.get(col, '').strip()
                record[key] = val
                if val:
                    has_data = True
            
            # Skip completely empty rows
            if not has_data:
                continue

            # Maintain the ISO array fallback specifically for your Exam Schedule sections
            if 'date' in record and 'iso' not in record:
                record['iso'] = [record['date']] if record['date'] else []
            elif 'iso' in record:
                parts = [d.strip() for d in record['iso'].split(';') if d.strip()]
                record['iso'] = parts if parts else ([record['date']] if record.get('date', '') else [])

            section_records.append(record)

        if section_records:
            final_json_structure[section] = {
                "pageTitle": page_title,
                "records": section_records
            }

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_json_structure, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
