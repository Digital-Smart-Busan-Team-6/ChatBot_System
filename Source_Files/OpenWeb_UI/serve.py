# ── serve.py 맨 위 5줄 정도만 추가 ─────────────────────────
import sys, pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent   # .../Source_Files
sys.path.append(str(BASE))                              # PYTHONPATH에 추가
# --------------------------------------------------------

from Model.Run_Model import main as build_pipeline      # ❌ Source_Files. 안 붙임
# 이제 정상 import



# serve.py  ─────────────────────────────────────────────
from fastapi import FastAPI
from langserve import add_routes

# 1) 우리 체인 준비 (retriever, llm 등 다 포함)
chain = build_pipeline(return_chain_only=True)   # main()에 옵션 하나 추가해 체인만 리턴하도록

# 2) FastAPI + OpenAI 호환 라우트
app = FastAPI()
add_routes(app, chain, path="/v1")  # /v1/chat/completions 엔드포인트 자동 생성

# run: uvicorn serve:app --host 0.0.0.0 --port 8000
