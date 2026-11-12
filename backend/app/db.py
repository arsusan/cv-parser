import sqlite3
from datetime import datetime, timezone
from .config import DB_PATH
from .prompts import DEFAULT_PROMPT


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _now():
    return datetime.now(timezone.utc).isoformat()


def _add_prompt(c, text):
    version = (c.execute('SELECT MAX(version) FROM prompts').fetchone()[0] or 0) + 1
    c.execute('UPDATE prompts SET is_active = 0')
    c.execute('INSERT INTO prompts(version, text, is_active, created_at) VALUES (?,?,1,?)',
              (version, text, _now()))
    return version


def init_db():
    with conn() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, version INTEGER, text TEXT,
            is_active INTEGER, created_at TEXT);
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, model TEXT,
            prompt_version INTEGER, status TEXT, input_tokens INTEGER,
            output_tokens INTEGER, cost_usd REAL, would_be_cost_usd REAL,
            duration_s REAL, result_json TEXT, validation_json TEXT,
            error TEXT, created_at TEXT);
        ''')
        if c.execute('SELECT COUNT(*) FROM prompts').fetchone()[0] == 0:
            _add_prompt(c, DEFAULT_PROMPT)


def get_active_prompt():
    with conn() as c:
        r = c.execute('SELECT version, text FROM prompts WHERE is_active = 1').fetchone()
    return r['version'], r['text']


def save_prompt(text):
    with conn() as c:
        return _add_prompt(c, text)


def reset_prompt():
    return save_prompt(DEFAULT_PROMPT)


def insert_run(**k):
    with conn() as c:
        cur = c.execute(
            'INSERT INTO runs(filename, model, prompt_version, status, input_tokens, '
            'output_tokens, cost_usd, would_be_cost_usd, duration_s, result_json, '
            'validation_json, error, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)',
            (k['filename'], k['model'], k['prompt_version'], k['status'], k['input_tokens'],
             k['output_tokens'], k['cost_usd'], k['would_be_cost_usd'], k['duration_s'],
             k['result_json'], k['validation_json'], k['error'], _now()))
        return cur.lastrowid


def list_runs(limit=50):
    with conn() as c:
        rows = c.execute(
            'SELECT id, filename, model, prompt_version, status, input_tokens, output_tokens, '
            'cost_usd, duration_s, created_at FROM runs ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
    return [dict(r) for r in rows]


def stats():
    with conn() as c:
        r = c.execute(
            'SELECT COUNT(*) n, COALESCE(SUM(cost_usd),0) cost, COALESCE(SUM(would_be_cost_usd),0) wb, '
            'COALESCE(SUM(input_tokens),0) i, COALESCE(SUM(output_tokens),0) o FROM runs').fetchone()
    return {'runs': r['n'], 'total_cost': r['cost'], 'total_would_be_cost': r['wb'],
            'input_tokens': r['i'], 'output_tokens': r['o']}