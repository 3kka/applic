#!/usr/bin/env python3
"""
convert.py — QuickPly RRB NTPC Schedule Compiler
Place this at the root of the 3kka/applic GitHub repository.

PURPOSE
-------
Downloads the Google Sheet as CSV (pandas handles RFC 4180 quoted fields
natively, so any cell containing a comma is parsed correctly with zero
custom code) and exports a clean, structured data.json.

EXPECTED SHEET COLUMNS (case-insensitive, spaces ignored)
----------------------------------------------------------
  event   Required. Name of the exam event.
  date    Required. Primary date in YYYY-MM-DD format (used for display).
  iso     Optional. Semicolon-separated ISO dates for multi-day events.
          If this column is absent, iso[] is derived from the date column.

          Example multi-day row:
          event=CBT Phase 1, date=2026-11-01, iso=2026-11-01;2026-11-02;2026-11-03

OUTPUT FORMAT (data.json)
-------------------------
[
  { "event": "IBPS PO (Mains)", "date": "2026-10-04", "iso": ["2026-10-04"] },
  { "event": "CBT Phase 1",     "date": "2026-11-01", "iso": ["2026-11-01","2026-11-02"] }
]
"""

import os
import sys
import json
import pandas as pd

RAW_DATA = os.environ.get('RAW_DATA')
OUTPUT_FILE = 'data.json'


def build_iso(date_val: str, iso_val: str) -> list:
    """
    Build the iso[] array for a single schedule row.
    Priority:
      1. Explicit 'iso' column value (semicolon-separated) if present.
      2. Single 'date' column value as fallback.
    """
    if iso_val:
        parts = [d.strip() for d in iso_val.split(';') if d.strip()]
        if parts:
            return parts
    if date_val:
        return [date_val]
    return []


def main():
    if not RAW_DATA:
        print('ERROR: RAW_DATA environment variable is not set or is empty.', file=sys.stderr)
        sys.exit(1)

    print(f'Parsing live sheet data from payload...')

    try:
        data_matrix = json.loads(RAW_DATA)
        if not data_matrix or len(data_matrix) < 2:
            print('ERROR: Sheet data is empty or missing headers.', file=sys.stderr)
            sys.exit(1)
            
        headers = data_matrix[0]
        rows = data_matrix[1:]
        df = pd.DataFrame(rows, columns=headers)
        
    except Exception as e:
        print(f'ERROR: Failed to parse RAW_DATA JSON: {e}', file=sys.stderr)
        sys.exit(1)

    print(f'Raw DataFrame shape: {df.shape[0]} rows × {df.shape[1]} columns')
    print(f'Columns found: {list(df.columns)}')

    # ── Normalize column names ────────────────────────────────────────────────
    # Lowercase + strip + collapse spaces so 'Event Name' → 'event_name'
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r'\s+', '_', regex=True)
    )

    # ── Validate required columns ─────────────────────────────────────────────
    required = {'event', 'date'}
    missing  = required - set(df.columns)
    if missing:
        print(f'ERROR: Sheet is missing required columns: {missing}', file=sys.stderr)
        print(f'       Columns present: {list(df.columns)}', file=sys.stderr)
        sys.exit(1)

    # ── Clean all cell values ─────────────────────────────────────────────────
    df = df.apply(lambda col: col.str.strip())  # Strip leading/trailing whitespace
    df = df.fillna('')                           # Eliminate any residual NaN

    # ── Drop completely empty rows ────────────────────────────────────────────
    df = df[df.apply(lambda row: any(v != '' for v in row), axis=1)]
    df = df.reset_index(drop=True)

    # ── Build JSON records ────────────────────────────────────────────────────
    has_iso_col = 'iso' in df.columns
    records     = []

    for _, row in df.iterrows():
        event_val = row.get('event', '').strip()
        date_val  = row.get('date',  '').strip()
        iso_val   = row.get('iso',   '').strip() if has_iso_col else ''

        # Skip rows with no event name (header duplicates, notes, etc.)
        if not event_val:
            continue

        records.append({
            'event': event_val,
            'date':  date_val,
            'iso':   build_iso(date_val, iso_val),
        })

    # ── Write output ──────────────────────────────────────────────────────────
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f'SUCCESS: {len(records)} records exported → {OUTPUT_FILE}')


if __name__ == '__main__':
    main()

