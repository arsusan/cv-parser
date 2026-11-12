from datetime import date


def _to_month(s, is_end=False):
    if not s:
        return None
    s = str(s).strip().lower()
    if s in ('present', 'current', 'now'):
        t = date.today()
        return t.year * 12 + t.month - 1
    try:
        parts = s[:7].split('-')
        y = int(parts[0])
        m = int(parts[1]) if len(parts) > 1 else (12 if is_end else 1)
        return y * 12 + m - 1
    except ValueError:
        return None


def total_years(experience: list):
    spans = []
    for e in experience:
        a = _to_month(e.get('start_date'))
        b = _to_month(e.get('end_date'), True)
        if a is None or b is None or b < a:
            continue
        spans.append((a, b + 1))
    if not spans:
        return None
    spans.sort()
    merged = [list(spans[0])]
    for a, b in spans[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return round(sum(b - a for a, b in merged) / 12, 1)