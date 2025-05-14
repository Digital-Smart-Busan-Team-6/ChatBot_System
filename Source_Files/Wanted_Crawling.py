# 임포트 해야하는 것
import time
import requests
from tqdm import tqdm
import pandas as pd
import json
from bs4 import BeautifulSoup
import re
from Data_Analysis import *

# 점핏 메인 페이지의 url입니다
MAIN_URL = "https://www.wanted.co.kr/wdlist?country=kr&job_sort=job.popularity_order&years=-1&locations=all/offset="
DETAIL_URL = 'https://jumpit.saramin.co.kr/position/'


'''
원티드 메인 페이지를 가져오는 함수입니다
json 형식으로 되어있는 페이지를 가져옵니다
페이지를 넘기면서 가져오고, 빈 페이지가 나올 때까지 반복합니다
'''


def get_wanted_main_crawling():
    offset = 0
    limit = 20
    posts = {}

    pbar = tqdm(desc="Fetching job posts", unit="post")

    while True:
        url = f"https://www.wanted.co.kr/api/chaos/navigation/v1/results?1747219507653=&country=kr&job_sort=job.popularity_order&years=-1&locations=all&limit={limit}&offset={offset}"
        response = requests.get(url)
        data = response.json()
        posts = mergeJsonDicts(posts, data)
        jobs = data.get("data", [])

        if not jobs:
            break  # 더 이상 데이터가 없으면 종료

        offset += limit  # 다음 페이지로
        pbar.update(len(jobs))  # tqdm bar 업데이트

    pbar.close()
    return posts

def get_wanted_detail_crawling(ids):
    posts_detail = {}
    pbar = tqdm(desc="Fetching Detail Contents", unit="post")

    for id in ids:
        url = f"https://www.wanted.co.kr/api/chaos/jobs/v4/{id}/details"
        response = requests.get(url)
        data_detail = response.json()
        posts_detail = mergeJsonDicts(posts_detail, data_detail)
        time.sleep(0.1)  # 요청 간에 잠시 대기
        pbar.update(1)
    pbar.close()
    return posts_detail


def get_tags_json(type):
    url = "https://static.wanted.co.kr/tags?tags="
    if type == "skill":
        url = url + type
    elif type == "category":
        url = url + type

    response = requests.get(url)
    tags = response.json()
    return tags

def get_ids(posts):
    ids = []
    for post in posts:
        id = post['id']
        ids.append(id)
    return ids

'''
Getter 함수들입니다
각각의 정보를 가져오는 함수들입니다
'''




# 날짜 입력 후 실행하면 'Crawling_DataFile_MainPage_20250503' 형식의 파일이 저장됨
# 저장 폴더는 Data_Files
# 해당 폴더는 gitignore에 추가되어있으니 올라가지 않을것임
def toCsvFile(dataFrame, date, type):
    dataFrame['date'] = pd.to_datetime(dataFrame['date'], format='%Y%m%d')
    dataFrame['date'] = dataFrame['date'].dt.strftime('%Y년-%m월-%d일')

    if type == 'Main':
        dataFrame.T.to_csv(f"../Data_Files/Crawling_DataFile_MainPage_Csv_{date}.txt",
                           sep='\t')
    elif type == 'Detail':
        dataFrame.T.to_csv(f"../Data_Files/Crawling_DataFile_DetailPage_Csv_{date}.txt",
                           sep='\t')
    elif type == 'Merge':
        dataFrame.T.to_csv(f"../Data_Files/Crawling_DataFile_MergePage_Csv_{date}.txt",
                           sep='\t')


def toJsonFile(dataFrame, date, type):
    dataFrame['date'] = date
    dataFrame['date'] = pd.to_datetime(dataFrame['date'], format='%Y%m%d')
    dataFrame['date'] = dataFrame['date'].dt.strftime('%Y년%m월%d일')
    if type == 'Main':
        dataFrame.T.to_json(f"../Data_Files/Crawling_DataFile_MainPage_json_{date}.txt",
                            force_ascii=False)
    elif type == 'Detail':
        dataFrame.T.to_json(f"../Data_Files/Crawling_DataFile_DetailPage_json_{date}.txt",
                            force_ascii=False)
    elif type == 'Merge':
        dataFrame.T.to_json(f"../Data_Files/Crawling_DataFile_MergePage_json_{date}.txt",
                            force_ascii=False)



'''
텍스트 전처리 함수
'''


def toImproveText(text):
    if isinstance(text, list):  # 입력이 리스트인지 확인
        cleaned_list = []
        for item in text:
            cleaned_item = item.replace('\r', '').replace('\t', '')
            # +, #, ,는 유지하면서 나머지 특수문자 제거
            cleaned_item = re.sub(r'[^a-zA-Z0-9가-힣\s+#,]', '', cleaned_item).strip()
            cleaned_list.append(cleaned_item)
        return cleaned_list
    elif isinstance(text, int):
        return text
    else:
        cleaned_text = text.replace('\r', '').replace('\t', '')
        cleaned_text = re.sub(r'[^a-zA-Z0-9가-힣\s+#,]', '', cleaned_text).strip()
        return cleaned_text


def toImproveDataFrame(data):
    columns = data.columns
    for column in columns:
        data[column] = data[column].apply(toImproveText)
    return data




