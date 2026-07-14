#!/usr/bin/env python3
"""Auto-publish: find next week's schedule JSON and update sidur_live.html."""
import json, re, sys
from datetime import date, timedelta
from pathlib import Path

SCHEDULES_DIR = Path(__file__).parent / 'schedules'
HTML_PATH = Path(__file__).parent / 'sidur_live.html'

# Find the Sunday that starts next week (or current week if today is Sat/Sun)
today = date.today()
days_to_sunday = (6 - today.weekday()) % 7  # days until next Sunday
if days_to_sunday == 0:
    days_to_sunday = 7
next_sunday = today + timedelta(days=days_to_sunday)

# Also try this Sunday (in case running early Saturday night)
this_sunday = today - timedelta(days=(today.weekday() + 1) % 7)
candidates = [next_sunday, this_sunday]

schedule = None
week_start = None
for candidate in candidates:
    json_path = SCHEDULES_DIR / f'{candidate.isoformat()}.json'
    if json_path.exists():
        schedule = json.loads(json_path.read_text(encoding='utf-8'))
        week_start = candidate.isoformat()
        print(f'Found schedule: {json_path.name} ({len(schedule["shifts"])} shifts)')
        break

if not schedule:
    available = sorted(SCHEDULES_DIR.glob('*.json'))
    print(f'ERROR: No schedule found for {next_sunday} or {this_sunday}')
    print(f'Available: {[p.name for p in available]}')
    sys.exit(1)

# Update scheduleData in HTML
data_str = json.dumps(schedule, ensure_ascii=False, indent=2)
new_block = f'let scheduleData = {data_str};'
html = HTML_PATH.read_text(encoding='utf-8')
updated = re.sub(r'let scheduleData = \{[\s\S]*?\n\};', new_block, html)
if updated == html:
    print('ERROR: scheduleData pattern not found'); sys.exit(1)

HTML_PATH.write_text(updated, encoding='utf-8')
print(f'Updated sidur_live.html: weekStart={week_start}')
