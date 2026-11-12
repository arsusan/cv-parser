import json
import time
from typing import TypedDict, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from pydantic import ValidationError

from . import config, db
from .extractors import extract_text
from .schemas import CVData
from .validators import validate
from .utils import total_years
from .cost import compute_cost


class State(TypedDict, total=False):
    filename: str
    file_bytes: bytes
    model: str
    prompt_text: str
    prompt_version: int
    started_at: float
    cv_text: str
    raw_output: str
    parsed: Optional[dict]
    error: Optional[str]
    attempts: int
    input_tokens: int
    output_tokens: int
    validation: dict
    result: Optional[dict]
    status: str
    cost: dict
    duration: float
    run_id: int


# ---------- nodes ----------
def n_extract(state: State):
    try:
        return {'cv_text': extract_text(state['filename'], state['file_bytes']), 'error': None}
    except Exception as e:
        return {'cv_text': '', 'error': f'Extraction failed: {e}'}


def n_llm(state: State):
    attempts = state.get('attempts', 0) + 1
    llm = ChatOpenAI(model=state['model'], api_key=config.OPENROUTER_API_KEY,
                     base_url=config.OPENROUTER_BASE_URL, temperature=0,
                     timeout=90, max_retries=0)
    msgs = [SystemMessage(content=state['prompt_text']),
            HumanMessage(content='CV TEXT:\n' + state['cv_text'])]
    if state.get('error') and state.get('raw_output'):  # repair attempt
        msgs += [AIMessage(content=state['raw_output']),
                 HumanMessage(content='Your previous answer was invalid: ' + state['error']
                              + '. Return ONLY the corrected JSON object.')]
    try:
        resp = llm.invoke(msgs)
        usage = resp.usage_metadata or {}
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        return {'attempts': attempts, 'raw_output': content, 'error': None,
                'input_tokens': state.get('input_tokens', 0) + usage.get('input_tokens', 0),
                'output_tokens': state.get('output_tokens', 0) + usage.get('output_tokens', 0)}
    except Exception as e:
        time.sleep(2)  # free models are often rate limited
        return {'attempts': attempts, 'raw_output': '', 'parsed': None, 'error': f'LLM error: {e}'}


def n_parse(state: State):
    raw = state.get('raw_output', '')
    if not raw:
        return {}  # LLM call failed, keep its error
    a, b = raw.find('{'), raw.rfind('}')  # also strips code fences and extra text
    if a == -1 or b <= a:
        return {'parsed': None, 'error': 'No JSON object found in the response'}
    try:
        parsed = json.loads(raw[a:b + 1])
    except json.JSONDecodeError as e:
        return {'parsed': None, 'error': f'Invalid JSON: {e}'}
    try:
        CVData.model_validate(parsed)
    except ValidationError as e:
        msg = '; '.join('.'.join(str(p) for p in x['loc']) + ' ' + x['msg'] for x in e.errors())
        return {'parsed': parsed, 'error': 'Schema errors: ' + msg}
    return {'parsed': parsed, 'error': None}


def n_validate(state: State):
    report = validate(state['parsed'], state['cv_text'])
    try:
        result = CVData.model_validate(state['parsed']).model_dump()
        computed = total_years(result['experience'])
        if computed is not None:
            result['years_of_experience'] = computed
    except ValidationError:
        result = state['parsed']
    return {'validation': report, 'result': result, 'status': report['status']}


def n_persist(state: State):
    duration = round(time.time() - state['started_at'], 2)
    cost = compute_cost(state['model'], state.get('input_tokens', 0), state.get('output_tokens', 0))
    validation = state.get('validation') or {
        'status': 'failed', 'errors': [state.get('error') or 'Unknown error'],
        'warnings': [], 'checks': {}}
    status = state.get('status') or 'failed'
    run_id = db.insert_run(
        filename=state['filename'], model=state['model'], prompt_version=state['prompt_version'],
        status=status, input_tokens=state.get('input_tokens', 0),
        output_tokens=state.get('output_tokens', 0), cost_usd=cost['total_cost'],
        would_be_cost_usd=cost['would_be_cost'], duration_s=duration,
        result_json=json.dumps(state.get('result')), validation_json=json.dumps(validation),
        error=state.get('error'))
    return {'duration': duration, 'cost': cost, 'validation': validation,
            'status': status, 'run_id': run_id}


# ---------- routing ----------
def route_after_extract(state: State):
    return 'fail' if state.get('error') else 'ok'


def route_after_parse(state: State):
    if state.get('error') and state['attempts'] < 1 + config.MAX_RETRIES:
        return 'retry'
    return 'validate' if state.get('parsed') is not None else 'fail'


# ---------- graph ----------
g = StateGraph(State)
g.add_node('extract_text', n_extract)
g.add_node('call_llm', n_llm)
g.add_node('parse_output', n_parse)
g.add_node('validate', n_validate)
g.add_node('persist', n_persist)
g.set_entry_point('extract_text')
g.add_conditional_edges('extract_text', route_after_extract, {'ok': 'call_llm', 'fail': 'persist'})
g.add_edge('call_llm', 'parse_output')
g.add_conditional_edges('parse_output', route_after_parse,
                        {'retry': 'call_llm', 'validate': 'validate', 'fail': 'persist'})
g.add_edge('validate', 'persist')
g.add_edge('persist', END)
graph = g.compile()


def run_pipeline(filename: str, data: bytes, model: str) -> dict:
    version, prompt_text = db.get_active_prompt()
    state = {'filename': filename, 'file_bytes': data, 'model': model,
             'prompt_text': prompt_text, 'prompt_version': version,
             'started_at': time.time(), 'attempts': 0,
             'input_tokens': 0, 'output_tokens': 0}
    # tags and metadata appear on the LangSmith trace (model + prompt version tracking)
    cfg = {'run_name': 'cv_parse',
           'tags': ['cv-parser', f'model:{model}', f'prompt:v{version}'],
           'metadata': {'model': model, 'prompt_version': version, 'filename': filename}}
    return graph.invoke(state, config=cfg)