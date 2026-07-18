#!/usr/bin/env python3
"""
convert.py — Dynamic Suffix-Based Schedule Compiler
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
        
        # Target Row 2 for headers, Row 3+ for data
        if not data_matrix or len(data_matrix) < 3:
            print('ERROR: Sheet data is empty or missing data rows.', file=sys.stderr)
            sys.exit(1)
            
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
    # Find all unique suffixes in the headers (e.g., extracting "RRB NTPC" from "Event - RRB NTPC")
    sections = set()
    for col in df.columns:
        if " - " in str(col):
            sections.add(str(col).split(" - ", 1)[1].strip())

    # ── PROCESS EACH SECTION INDEPENDENTLY ───────────────────────────────────
    for section in sections:
        # Construct the exact column names expected for this specific section
        event_col = f"Event - {section}"
        date_col = f"Date - {section}"
        iso_col = f"ISO - {section}"

        # Only process if both primary columns exist for this suffix
        if event_col in df.columns and date_col in df.columns:
            section_records = []
            
            for _, row in df.iterrows():
                event_val = row.get(event_col, '').strip()
                date_val = row.get(date_col, '').strip()
                iso_val = row.get(iso_col, '').strip() if iso_col in df.columns else ''

                # Skip empty rows for this specific section
                if not event_val:
                    continue

                section_records.append({
                    'event': event_val,
                    'date': date_val,
                    'iso': build_iso(date_val, iso_val)
                })
            
            # Map the clean records to the exact suffix name
            if section_records:
                final_json_structure[section] = section_records

    # ── WRITE OUTPUT ─────────────────────────────────────────────────────────
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_json_structure, f, ensure_ascii=False, indent=2)

    print(f'SUCCESS: Data exported → {OUTPUT_FILE}')

if __name__ == '__main__':
    main()
