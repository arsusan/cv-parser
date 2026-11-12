import time
import httpx
from .config import OPENROUTER_BASE_URL

_cache = {'t': 0.0, 'models': {}}


def _fetch() -> dict:
    if _cache['models'] and time.time() - _cache['t'] < 3600:
        return _cache['models']
    r = httpx.get(f'{OPENROUTER_BASE_URL}/models', timeout=20)
    r.raise_for_status()
    _cache['models'] = {m['id']: m for m in r.json()['data']}
    _cache['t'] = time.time()
    return _cache['models']


def _price(model_id):  # (prompt, completion) USD per token
    try:
        p = _fetch().get(model_id, {}).get('pricing', {})
        return float(p.get('prompt') or 0), float(p.get('completion') or 0)
    except Exception:
        return 0.0, 0.0


def list_models() -> list:
    out = []
    for m in _fetch().values():
        pi, po = _price(m['id'])
        out.append({'id': m['id'], 'name': m.get('name', m['id']),
                    'free': pi == 0 and po == 0,
                    'prompt_price': pi, 'completion_price': po})
    out.sort(key=lambda x: (not x['free'], x['id']))
    return out


def compute_cost(model_id, in_tokens, out_tokens) -> dict:
    pi, po = _price(model_id)
    actual = in_tokens * pi + out_tokens * po
    bi, bo = _price(model_id.removesuffix(':free'))
    would_be = in_tokens * bi + out_tokens * bo
    return {'input_cost': in_tokens * pi, 'output_cost': out_tokens * po,
            'total_cost': actual, 'would_be_cost': would_be, 'is_free': actual == 0}