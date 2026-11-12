import os
from dotenv import load_dotenv

load_dotenv()  # must run before LangChain reads the LANGSMITH_* variables

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'meta-llama/llama-3.3-70b-instruct:free')
DB_PATH = os.getenv('DB_PATH', 'cvparser.db')
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '2'))