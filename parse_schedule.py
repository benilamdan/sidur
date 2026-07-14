#!/usr/bin/env python3
"""Parse weekly schedule Excel and update sidur_live.html + schedules/YYYY-MM-DD.json."""
import sys, json, re, openpyxl
from datetime import datetime, timedelta
from pathlib import Path

excel_path = sys.argv[1]
week_start = sys.argv[2]  # YYYY-MM-DD

wb = openpyxl.load_workbook(excel_path, data_only=True)
ws = wb.worksheets[0]

SKIP = {'-', '--', ' ', '', None}

target_date = datetime.strptime(week_start, '%Y-%m-%d')

# Row 2 contains dates; find which columns match the 7 days of target week
day_cols = {}
for col in range(1, ws.max_column + 1):
    v = ws.cell(2, col).value
    if isinstance(v, datetime):
        for d in range(7):
            if v.date() == (target_date + timedelta(days=d)).date():
                day_cols[d] = col

if not day_cols:
    print(f'ERROR: week {week_start} not found in row 2 of excel')
    sys.exit(1)

print(f'Found days: {sorted(day_cols.keys())} => cols {[day_cols[d] for d in sorted(day_cols)]}')

# Col B (openpyxl=2) = first name, Col C (openpyxl=3) = family name
shifts = []
for row in range(3, ws.max_row + 1):
    fname = ws.cell(row, 2).value
    lname = ws.cell(row, 3).value
    parts = [str(x).strip() for x in [fname, lname] if x is not None and str(x).strip()]
    name = ' '.join(parts).strip()
    if not name:
        continue
    # Skip header-like rows
    if name in ('שם משפחה', 'שם', 'קישור לחופש'):
        continue
    for day, col in day_cols.items():
        v = ws.cell(row, col).value
        if v is None:
            continue
        v = str(v).strip()
        if v in SKIP:
            continue
        shifts.append({'day': day, 'role': v, 'name': name, 'note': ''})

print(f'Parsed {len(shifts)} shifts')

schedule_data = {'weekStart': week_start, 'shifts': shifts}

# Save to schedules/YYYY-MM-DD.json
schedules_dir = Path(__file__).parent / 'schedules'
schedules_dir.mkdir(exist_ok=True)
json_path = schedules_dir / f'{week_start}.json'
json_path.write_text(json.dumps(schedule_data, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Saved {json_path}')

# Update sidur_live.html
data_str = json.dumps(schedule_data, ensure_ascii=False, indent=2)
new_block = f'let scheduleData = {data_str};'

html_path = Path(__file__).parent / 'sidur_live.html'
html = html_path.read_text(encoding='utf-8')
updated = re.sub(r'let scheduleData = \{[\s\S]*?\n\};', new_block, html)

if updated == html:
    print('ERROR: scheduleData pattern not found in HTML')
    sys.exit(1)

html_path.write_text(updated, encoding='utf-8')
print(f'Updated sidur_live.html: weekStart={week_start}, {len(shifts)} shifts')
