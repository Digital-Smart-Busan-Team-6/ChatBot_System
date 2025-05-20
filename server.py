import os
from pathlib import Path
from dotenv import load_dotenv


# 프로젝트 루트 디렉토리
BASE_DIR = Path(__file__).resolve().parent

# .env 파일 로드
load_dotenv(BASE_DIR / '.env')

# OpenAI 및 LangSmith 환경변수 설정
os.environ['OPENAI_API_KEY']   = os.getenv('OPENAI_API_KEY')
os.environ['LANGSMITH_ENDPOINT'] = os.getenv('LANGSMITH_ENDPOINT')
os.environ['LANGSMITH_PROJECT']  = os.getenv('LANGSMITH_PROJECT')
os.environ['LANGSMITH_TRACING']  = os.getenv('LANGSMITH_TRACING')
os.environ['LANGSMITH_API_KEY']  = os.getenv('LANGSMITH_API_KEY')

from fastapi import FastAPI
from langserve import add_routes
from app import get_chain
# 원본 문서가 저장된 폴더
DATA_DIR    = BASE_DIR / 'Data_Files'
# 벡터 DB가 저장된 폴더
chunk_size = int(os.getenv("CHUNK_SIZE","1000"))
kind       = os.getenv("KIND","json")
model_db_dir = BASE_DIR / os.getenv("DATA_PATH") / f'{kind}_{chunk_size}'

# FastAPI 앱 생성 및 라우트 추가
app = FastAPI()
add_routes(app, get_chain())
