'''
RAG_architecture(text_splitter)의 
문서 로드부터 스플릿, 임베딩 이전까지 바꿔 사용.
'''
import os
from glob import glob

# 텍스트 분할
from langchain_text_splitters import RecursiveJsonSplitter

input_max_chunk = 1000

splitter = RecursiveJsonSplitter(max_chunk_size=input_max_chunk)

# 폴더 아래에 있는 json파일 전부 다 열기
import json
import requests

# 폴더 경로 지정
filePath = './Data_Files(json)'
filetype = 'json'

# 해당 디렉토리 아래에 있는 파일들의 경로를 저장하는 함수와 리스트 생성
def list_files_recursively(directory):
    jsonFileName = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            jsonFileName.append(os.path.join(root, file))
    return jsonFileName

jsonFileName = list_files_recursively(filePath)

# 읽어 온 파일들 하나의 변수에 저장
docs = {}   #allData

for i in range(len(jsonFileName)):
    data = open(jsonFileName[i],'r', encoding='utf-8')
    json_data = json.load(data)
    docs.update(json_data)

# 문서 분할
texts = splitter.create_documents(texts = [docs],ensure_ascii = False)

# len(texts) # 문서 개수 확인