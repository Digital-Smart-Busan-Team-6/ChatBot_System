# ChatBot_System/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# 종속성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY Source_Files/ ./Source_Files/

# OpenWebUI용 serve 앱 실행
CMD ["uvicorn", "Source_Files.OpenWeb_UI.serve:app", "--host", "0.0.0.0", "--port", "8000"]



# 1) OS 패키지 업데이트 & JDK 설치
RUN apt-get update \
 && apt-get install -y default-jdk \
 && rm -rf /var/lib/apt/lists/*

# 2) JAVA_HOME 설정
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH="$JAVA_HOME/bin:$PATH"

# 3) 작업 디렉터리
WORKDIR /app

# 4) 파이썬 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) 소스 복사
COPY . /app
