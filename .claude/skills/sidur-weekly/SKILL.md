---
name: sidur-weekly
description: >
  עדכון שבועי של סידור עבודה טקסטיל וולפסון. השתמש בסקיל הזה בכל פעם שהמשתמש מעלה קובץ Excel של סידור עבודה (sidur*.xlsx),
  אפילו אם הוא אומר רק "הכנסתי" / "תעדכן" / "תעלה" עם קובץ xlsx. הסקיל מחליט אוטומטית:
  שבוע נוכחי → עדכון HTML חי + push. שבוע עתידי → שמירת JSON בלבד לפרסום אוטומטי שבת.
---

# סידור עבודה — תהליך שבועי

## מה הסקיל עושה

1. **מפרסר את ה-Excel** → JSON בפורמט `schedules/YYYY-MM-DD.json`
2. **מחליט**: שבוע נוכחי (weekStart ≤ היום) → מעדכן HTML חי + push. שבוע עתידי → JSON בלבד.
3. **מוודא** גלית עזר אוזר = `ב` (בוקר) בכל המשמרות שלה.
4. **Push לגיטהאב** — האתר מתעדכן תוך 2-3 דקות.

## קבצים קריטיים

- **קובץ מקור עם key**: `C:\Users\beny\Documents\קלוד\sidur_live.html` — מכיל OneSignal REST key
- **ריפו**: `C:\Users\beny\Documents\קלוד\sidur-repo\`
- **OneSignal key**: שמור רק ב-`C:\Users\beny\Documents\קלוד\sidur_live.html` — חפש ב-regex `os_v2_app_[a-z0-9]+`
- **Live URL**: `https://benilamdan.github.io/sidur/sidur_live.html`

## מבנה Excel — שתי אפשרויות

### פורמט A (sidur 1-7 style):
- שורה 1: כותרות עמודות (כולל `יום ראשון` עד `שבת`)
- שורה 2: תאריכים (datetime objects) בעמודות D-J
- שורות 3+: מספר, שם, משפחה, משמרות D-J (day 0-6)
- עמודות: `[3,4,5,6,7,8,9]` = ימים 0-6

### פורמט B (סידור_עבודה_טקסטיל style):
- שורה 1: כותרת כללית
- שורה 2: headers (שם, משפחה, יום ראשון...)
- שורה 3: תאריכים כ-string ("09/08/2026")
- שורות 4+: שם, משפחה, משמרות בעמודות C-I
- עמודות: `[2,3,4,5,6,7,8]` = ימים 0-6

**זיהוי פורמט**: אם row[0] של שורה 3 הוא int → פורמט A. אחרת → פורמט B.

## הערות חשובות

- ערכים לדלג עליהם: `None, '-', '--', ' ', ''`
- weekStart = התאריך של יום ראשון הראשון בקובץ
- אם weekStart ≤ היום: עדכן HTML חי
- אם weekStart > היום: JSON בלבד (שבת ה-Action יפרסם אוטומטית)
- **לפני push**: `git pull --ff-only` תמיד
- **אם push נדחה**: `git pull --rebase` ואז push מחדש — לא `reset --hard`
- **remote URL**: `https://github.com/benilamdan/sidur.git`

## קוד Python לפרסר

```python
import openpyxl, json, re, datetime as dt
from pathlib import Path
from datetime import date

def parse_sidur(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(min_row=1, max_row=4, values_only=True))
    
    # Detect format
    if isinstance(rows[2][0], int):  # Format A: row3[0] is employee number
        data_start = 3
        day_cols = [3,4,5,6,7,8,9]
        name_cols = (1, 2)
        # week_start from row2 dates
        for cell in rows[1][3:]:
            if isinstance(cell, dt.datetime):
                week_start = cell.strftime('%Y-%m-%d')
                break
    else:  # Format B
        data_start = 4
        day_cols = [2,3,4,5,6,7,8]
        name_cols = (0, 1)
        # week_start from row3 strings or datetimes
        for cell in rows[2][2:]:
            if isinstance(cell, dt.datetime):
                week_start = cell.strftime('%Y-%m-%d')
                break
            elif isinstance(cell, str) and '/' in cell:
                parts = cell.split('/')
                week_start = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                break
    
    SKIP = {None, '-', '--', ' ', ''}
    shifts = []
    for row in ws.iter_rows(min_row=data_start+1, values_only=True):
        fn, ln = name_cols
        first = str(row[fn]).strip() if row[fn] else ''
        last = str(row[ln]).strip() if row[ln] else ''
        if not first or first in {'None', 'שם', ''}: continue
        # Skip if it's a number-only first column in format A
        if isinstance(rows[2][0], int) and not isinstance(row[0], int): continue
        name = f"{first} {last}".strip()
        for day_idx, col in enumerate(day_cols):
            role = row[col]
            if role is None: continue
            role = str(role).strip()
            if role in SKIP: continue
            shifts.append({"day": day_idx, "role": role, "name": name, "note": ""})
    
    return week_start, shifts
```

## תהליך מלא

### 1. פרסר
```python
week_start, shifts = parse_sidur(xlsx_path)
schedule = {"weekStart": week_start, "shifts": shifts}
json.dump(schedule, open(f'sidur-repo/schedules/{week_start}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
```

### 2. בדוק גלית
```python
galit = [s for s in shifts if 'גלית' in s['name']]
# כל המשמרות של גלית חייבות להיות "ב"
```

### 3. החלט: שבוע נוכחי או עתידי?
```python
from datetime import date
is_current = date.fromisoformat(week_start) <= date.today()
```

### 4א. שבוע נוכחי — עדכן HTML
```python
import re
local_html = open(r'C:\Users\beny\Documents\קלוד\sidur_live.html', encoding='utf-8').read()
shifts_js = json.dumps(shifts, ensure_ascii=False, indent=2)
new_block = f'let scheduleData = {{\n  "weekStart": "{week_start}",\n  "shifts": {shifts_js}\n}};'
pattern = r'let scheduleData = \{[\s\S]*?\n\};'
new_html = re.sub(pattern, new_block, local_html, count=1)
import re as _re
KEY = _re.search(r'os_v2_app_[a-z0-9]+', local_html).group()
new_html = new_html.replace(KEY, '')
open(r'C:\Users\beny\Documents\קלוד\sidur-repo\sidur_live.html', 'w', encoding='utf-8').write(new_html)
```

### 5. Git push
```bash
cd "C:\Users\beny\Documents\קלוד\sidur-repo"
git pull --ff-only
git add schedules/{week_start}.json sidur_live.html version.json  # or just JSON if future
git commit -m "סידור שבוע {week_start} — {len(shifts)} משמרות"
git push
```

### 6. אמת באתר החי
```bash
until curl -s https://benilamdan.github.io/sidur/sidur_live.html | grep -q '"weekStart": "{week_start}"'; do sleep 10; done
```
(רק אם עדכנת HTML)
