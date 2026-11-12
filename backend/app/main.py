from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import config, db
from .cost import list_models
from .graph import run_pipeline
from .prompts import DEFAULT_PROMPT

db.init_db()
app = FastAPI(title='CV Parser API')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000'],
                   allow_methods=['*'], allow_headers=['*'])


class PromptIn(BaseModel):
    text: str


@app.get('/health')
def health():
    return {'ok': True, 'default_model': config.DEFAULT_MODEL}


@app.get('/models')
def models():
    try:
        return list_models()
    except Exception as e:
        raise HTTPException(502, f'Could not load models from OpenRouter: {e}')


@app.get('/prompt')
def get_prompt():
    version, text = db.get_active_prompt()
    return {'version': version, 'text': text, 'is_default': text == DEFAULT_PROMPT}


@app.put('/prompt')
def put_prompt(body: PromptIn):
    if not body.text.strip():
        raise HTTPException(400, 'Prompt cannot be empty')
    return {'version': db.save_prompt(body.text), 'text': body.text}


@app.post('/prompt/reset')
def reset_prompt():
    return {'version': db.reset_prompt(), 'text': DEFAULT_PROMPT}


@app.post('/parse')
def parse(file: UploadFile = File(...), model: str = Form(config.DEFAULT_MODEL)):
    name = file.filename or ''
    if not name.lower().endswith(('.pdf', '.docx')):
        raise HTTPException(400, 'Upload a PDF or DOCX file')
    data = file.file.read()
    if len(data) > 5 * 1024 * 1024:
        raise HTTPException(413, 'File too large (max 5 MB)')
    out = run_pipeline(name, data, model)
    keys = ['run_id', 'status', 'model', 'prompt_version', 'result', 'validation',
            'cost', 'duration', 'input_tokens', 'output_tokens', 'attempts', 'error', 'raw_output']
    return {k: out.get(k) for k in keys}


@app.get('/runs')
def runs():
    return db.list_runs()


@app.get('/stats')
def stats():
    return db.stats()