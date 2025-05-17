# Dockerfile  (ChatBot_System/Dockerfile)
FROM python:3.12-slim

WORKDIR /app

# 파이썬 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드
COPY Source_Files/ ./Source_Files/

# FastAPI 서버 실행
CMD ["uvicorn", "Source_Files.OpenWeb_UI.serve:app", "--host", "0.0.0.0", "--port", "8000"]
