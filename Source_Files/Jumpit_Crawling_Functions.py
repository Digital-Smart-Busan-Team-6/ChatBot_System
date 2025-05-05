# 임포트 해야하는 것
import time
import requests
from tqdm import tqdm
import pandas as pd
import json
from bs4 import BeautifulSoup

# 점핏 메인 페이지의 url입니다
MAIN_URL = "https://jumpit-api.saramin.co.kr/api/positions?sort=rsp_rate&highlight=false&page="


'''
점핏 메인 페이지를 가져오는 함수입니다
전체 공고의 제목, 회사 이름, 업무 종류, 테크 스택을 리턴 시켜 줍니다
title, company, jobCategory, techStacks = getJumpitMainPage() 형식
'''

'''
def getJumpitMainPage():
    allTechStacks = []
    allJobCategory = []
    allTitle = []
    allCompanyName = []
    i = 1
    isEmpty = False
    pbar = tqdm()
    # 빈 페이지까지 반복문 실행
    while(isEmpty == False):
        page = requests.get(MAIN_URL + str(i))
        soup = BeautifulSoup(page.content, "lxml")  # lxml Parser 사용
        json_text = soup.find('p').text
        data = json.loads(json_text)  # json 형식으로 변환 

        isEmpty = data['result']['emptyPosition']  # 빈 페이지인지 체크

        result = data['result']  
        positions = result['positions']  # result 안의 positions 리스트를 데이터 딕셔너리 형태로 모두 가져옴
        
        # 내용들 긁어와서 리스트 형태로 변환
        companyName = [position['companyName'] for position in positions] 
        techStacks = [position['techStacks'] for position in positions]  
        job_category = [position['jobCategory'] for position in positions]
        title = [position['title'] for position in positions] 
        
        # 각 공고문마다 긁어온 데이터들을 한 리스트에 넣어줌
        allTechStacks.extend(techStacks)  # allTechStack에 techStacks들 붙이기
        allJobCategory.extend(job_category)
        allTitle.extend(title)
        allCompanyName.extend(companyName)
        
        pbar.update(1)  # 진행 상황 확인 위한 바 업데이트   
        time.sleep(0.5)  # 크롤링 매크로 탐지 방지 위해 sleep
        i += 1
    print('모든 페이지 정보를 가져 왔습니다')
    return allTitle, allCompanyName, allJobCategory, allTechStacks
'''

'''
점핏 메인 페이지를 가져오는 함수입니다
xml 형식으로 되어있는 페이지의 Positions를 가져옵니다
페이지를 넘기면서 가져오고, 빈 페이지가 나올 때까지 반복합니다
'''
def getJumpitPositions():
    isEmpty = False
    positions = []
    i = 1
    while(isEmpty == False):
        pbar = tqdm(total=None, desc="Loading", unit="page")  # 진행률 표시줄 초기화
        page = requests.get(MAIN_URL + str(i))
        soup = BeautifulSoup(page.content, "lxml")  # lxml Parser 사용
        json_text = soup.find('p').text
        data = json.loads(json_text)  # json 형식으로 변환 

        isEmpty = data['result']['emptyPosition']  # 빈 페이지인지 체크

        result = data['result']  
        positions.extend(result['positions'])  # result 안의 positions 리스트를 데이터 딕셔너리 형태로 모두 가져옴
        i += 1
        pbar.update(1)  # 진행률 표시줄 업데이트
    print('모든 페이지 정보를 가져 왔습니다')
    return positions

# def_toJson(positions):

'''
Getter 함수들입니다
각각의 정보를 가져오는 함수들입니다
'''
def getTitles(positions):
    titles = []
    for position in positions:
        title = position['title']
        titles.append(title)
    return titles

def getCompanyNames(positions):
    companyNames = []
    for position in positions:
        companyName = position['companyName']
        companyNames.append(companyName)
    return companyNames

def getJobCategories(positions):
    jobCategories = []
    for position in positions:
        jobCategory = position['jobCategory']
        jobCategories.append(jobCategory)
    return jobCategories

def getTechStacks(positions):
    techStacks = []
    for position in positions:
        techStack = position['techStacks']
        techStacks.append(techStack)
    return techStacks


def getJobLocations(positions):
    jobLocations = []
    for position in positions:
        jobLocation = position['locations']
        jobLocations.append(jobLocation)
    return jobLocations

def getMinCareer(positions):
    minCareers = []
    for position in positions:
        minCareer = position['minCareer']
        minCareers.append(minCareer)
    return minCareers

def getMaxCareer(positions):
    maxCareers = []
    for position in positions:
        maxCareer = position['maxCareer']
        maxCareers.append(maxCareer)
    return maxCareers

def getIDs(positions):
    ids = []
    for position in positions:
        id = position['id']
        ids.append(id)
    return ids

def getClosedAt(positions):
    closedAts = []
    for position in positions:
        closedAt = position['closedAt']
        closedAts.append(closedAt)
    return closedAt


# 날짜 입력 후 실행하면 'Crawling_DataFile_MainPage_20250503' 형식의 파일이 저장됨
# 저장 폴더는 Data_Files
# 해당 폴더는 gitignore에 추가되어있으니 올라가지 않을것임
def toCsvFile(dataFrame, date):
    dataFrame.to_csv(f"../Data_Files/Crawling_DataFile_MainPage_Csv_{date}", header=False, sep='\t')

def toJsonFile(dataFrame, date):
    dataFrame.to_json(f"../Data_Files/Crawling_DataFile_MainPage_json_{date}",force_ascii=False)
