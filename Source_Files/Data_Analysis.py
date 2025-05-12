import pandas as pd
import json
import os

from debugpy.common.util import force_ascii


def getNewPost(DataFrameBefore, DataFrameNew):
    newPost = DataFrameNew[~DataFrameNew.index.isin(DataFrameBefore.index)]

    return newPost

def getClosedPost(DataFrameBefore, DataFrameNew):
    closedPost = DataFrameBefore[~DataFrameBefore.index.isin(DataFrameNew.index)]

    return closedPost

# main, detail DataFrame을 합치는 함수입니다
def combineDataFrames(mainDataFrame, detailDataFrame):
    combinedDataFrame = pd.merge(detailDataFrame, mainDataFrame,
                                 left_index=True,
                                 right_index=True)

    return combinedDataFrame


# 파일 경로
#file_path = "/mnt/data/Crawling_DataFile_MergePage_json_20250512_test.txt"

# 파일 열기 및 로드
#with open(file_path, "r", encoding="utf-8") as f:
#    data = json.load(f)

# 평문 생성 함수 정의
def generate_plain_text(entry):
    title = entry.get("title", "")
    company = entry.get("company", "")
    location = ", ".join(entry.get("jobLocation", []))
    date = entry.get("date", "")
    closed_at = entry.get("closedAt", "")
    category = entry.get("jobCategory", "")
    min_career = entry.get("minCareer", 0)
    max_career = entry.get("maxCareer", 0)

    # 주요 업무
    main_work = " ".join([w.strip() for w in entry.get("mainWork", []) if w.strip()])

    # 자격 요건
    requirements = " ".join([r.strip() for r in entry.get("requirements", []) if r.strip()])

    # 우대 사항
    preferential = " ".join([p.strip() for p in entry.get("preferential", []) if p.strip()])

    # 복지 및 혜택
    welfare = " ".join([w.strip() for w in entry.get("welfare", []) if w.strip()])

    # 지원 절차
    procedures = " ".join([p.strip() for p in entry.get("procedures", []) if p.strip()])

    # 학력
    education = entry.get("education", "")

    # 기술 스택
    techstack = ", ".join(entry.get("techStack", []))

    # 특이사항
    pride = ", ".join(entry.get("pride", []))

    # 평문 구성
    text = (
        f"{company}는 {title} 포지션을 모집하고 있습니다. 이 포지션은 {location}에서 근무하게 되며, "
        f"최소 {min_career}년에서 최대 {max_career}년까지의 경력을 요구합니다. 해당 공고는 {date}에 게시되었으며, 마감일은 {closed_at}입니다. "
        f"주요 직무는 {category}입니다. "
        f"주요 업무로는 {main_work} 등이 있습니다. "
        f"자격 요건은 다음과 같습니다. {requirements} "
        f"우대 사항으로는 {preferential} 등이 있으며, "
        f"복지 및 혜택으로는 {welfare} 등이 제공됩니다. "
        f"지원 절차는 다음과 같습니다. {procedures} "
        f"학력 요건은 {education}이며, "
        f"요구 기술 스택은 {techstack}입니다. "
    )
    if pride:
        text += f"특이사항으로는 {pride} 등이 있습니다. "
    return text.strip()

# 전체 평문 리스트 생성
#plain_texts = [generate_plain_text(entry) for entry in data.values()]

#plain_texts[:2]  # 상위 2개 예시 출력

def check_format(data):
    """주어진 문자열이 JSON 형식인지 텍스트 형식인지 확인합니다."""
    try:
        json.loads(data)
        return "JSON"
    except json.JSONDecodeError:
        return "Text"


import json
import pandas as pd


def save_dataframe_to_json(df, file_path):
    """
    Pandas DataFrame을 JSON 형식으로 저장합니다.
    파일이 이미 존재하면 데이터를 추가하고, 존재하지 않으면 새로 생성합니다.
    Args:
        df (pd.DataFrame): 저장할 DataFrame입니다.
        file_path (str): JSON 파일의 경로입니다.
    """
    try:
        # DataFrame을 JSON 객체로 변환합니다. orient='index'를 사용하여 인덱스를 키로 사용합니다.
        new_data = df.to_dict(orient='index')

        # 파일이 이미 존재하는 경우
        if os.path.exists(file_path):
            # 파일을 읽어 기존 JSON 데이터를 로드합니다.
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)  # JSON 객체 형태로 읽음
                except json.JSONDecodeError:
                    existing_data = {}  # 파일이 비어 있거나 유효한 JSON이 아닌 경우 빈 객체로 처리

            # 기존 데이터에 새 데이터를 병합합니다.  기존에 있던 키는 덮어쓰게 됩니다.
            existing_data.update(new_data)

            # 수정된 데이터를 파일에 씁니다.
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=4)
            print(f"DataFrame을 '{file_path}'에 추가하여 저장했습니다.")

        # 파일이 존재하지 않는 경우
        else:
            # JSON 객체를 파일에 씁니다.
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)
            print(f"DataFrame을 '{file_path}'에 새로 저장했습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")


def write_text_to_file(file_path, text_data, append=True):
    """텍스트 데이터를 파일에 쓰거나 추가합니다."""
    try:
        mode = "a" if append else "w"
        with open(file_path, mode, encoding="utf-8") as f:
            f.write(text_data)
        print(f"텍스트 데이터가 '{file_path}'에 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"오류 발생: {e}")

def to_data_file(data):
    """주어진 데이터를 파일에 저장합니다. JSON 또는 텍스트 형식에 따라 처리합니다."""
    filePathJson = "../Data_Files/Data_Analysis_json.txt"  # 파일 경로 상수화
    filePathText = "../Data_Files/Data_Analysis_text.txt"


    data_type = check_format(data)

    if data_type == "JSON":
        mergeJson = merge_json_from_file(filePathJson, data)  # Use the helper function
        mergeJson.to_json(filePathJson, force_ascii=False)
    elif data_type == "Text":
        write_text_to_file(filePathText, data)  # Use the helper function
    else:
        print("지원하지 않는 데이터 형식입니다.")  # Handle other cases

