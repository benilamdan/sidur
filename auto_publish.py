#!/usr/bin/env python3
import json, re, sys
from datetime import date, timedelta
from pathlib import Path

repo_dir = Path(__file__).parent

# Find next Sunday
today = date.today()
days_to_sunday = (6 - today.weekday()) % 7
if days_to_sunday == 0:
    days_to_sunday = 7
next_sunday = today + timedelta(days=days_to_sunday)

schedule_file = repo_dir / 'schedules' / f'{next_sunday}.json'
if not schedule_file.exists():
    print(f"No schedule file: {schedule_file} — skipping")
    sys.exit(0)

print(f"Found schedule: {schedule_file.name} ({len(json.loads(schedule_file.read_text(encoding='utf-8'))['shifts'])} shifts)")

schedule = json.loads(schedule_file.read_text(encoding='utf-8'))

html_file = repo_dir / 'sidur_live.html'
html = html_file.read_text(encoding='utf-8')

shifts_js = json.dumps(schedule['shifts'], ensure_ascii=False, indent=2)
new_block = f'let scheduleData = {{\n  "weekStart": "{schedule["weekStart"]}",\n  "shifts": {shifts_js}\n}};'

pattern = r'let scheduleData = \{[\s\S]*?\n\};'
new_html = re.sub(pattern, new_block, html, count=1)
if new_html == html:
    print("ERROR: scheduleData block not found in HTML")
    sys.exit(1)

html_file.write_text(new_html, encoding='utf-8')
print(f"Updated sidur_live.html: weekStart={schedule['weekStart']}")

ts = today.strftime('%Y%m%d')
version_file = repo_dir / 'version.json'
version_file.write_text(json.dumps({"ts": ts}), encoding='utf-8')
print(f"Updated version.json: ts={ts}")
