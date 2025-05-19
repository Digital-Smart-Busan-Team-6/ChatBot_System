# -------- import & helpers ------------------------------------
from pathlib import Path
import json, os
from dotenv import load_dotenv
from langchain.schema import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_text_splitters import RecursiveCharacterTextSplitter, RecursiveJsonSplitter
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain.retrievers import EnsembleRetriever
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from konlpy.tag import Okt
import pandas as pd
from setting_metadata import *


def load_env_variables_for_Local():
    """
    .env 파일에서 환경 변수를 로드합니다.
    """
    # .env 파일의 경로를 지정합니다.
    # 현재 스크립트의 상대 경로로 설정합니다.
    # load_dotenv(dotenv_path='../../.env')
    # 절대 경로로 설정합니다.
    load_dotenv(dotenv_path='../../.env')

    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
    os.environ['LANGSMITH_ENDPOINT'] = os.getenv('LANGSMITH_ENDPOINT')
    os.environ['LANGSMITH_PROJECT'] = os.getenv('LANGSMITH_PROJECT')
    os.environ['LANGSMITH_TRACING'] = os.getenv('LANGSMITH_TRACING')
    os.environ['LANGSMITH_API_KEY'] = os.getenv('LANGSMITH_API_KEY')


def load_env_variables_for_Colab():
    from google.colab import userdata
    os.environ['OPENAI_API_KEY'] = userdata.get('OPENAI_API_KEY')
    os.environ['LANGSMITH_ENDPOINT'] = userdata.get('LANGSMITH_ENDPOINT2')
    os.environ['LANGSMITH_PROJECT'] = userdata.get('LANGSMITH_PROJECT2')
    os.environ['LANGSMITH_TRACING'] = userdata.get('LANGSMITH_TRACING')
    os.environ['LANGSMITH_API_KEY'] = userdata.get('LANGSMITH_API_KEY2')


# ---------- tokenizers ----------------------------------------
okt = Okt()


def len_okt(t):  return len(okt.morphs(t))


def okt_tokenize(t): return okt.morphs(t)


# ---------- 1. 로더 -------------------------------------------


import os, json
from langchain.schema import Document
from langchain_community.document_loaders import DirectoryLoader


def load_files(file_path: str, kind: str) -> list[Document]:
    docs = []

    # 1) JSON 처리
    if kind in ("json", "all"):
        json_files = [f for f in os.listdir(file_path) if f.endswith(".json")]
        analysis_files = [f for f in json_files if "Analysis" in f]
        post_files = [f for f in json_files if "improve" in f]

        if analysis_files:
            with open(os.path.join(file_path, analysis_files[0]), encoding="utf-8") as f:
                data_analysis = json.load(f)
            docs += make_analysis_docs(data_analysis)

        if post_files:
            with open(os.path.join(file_path, post_files[0]), encoding="utf-8") as f:
                raw = json.load(f)

            # ◀ 리스트면 dict로 변환 ▶
            if isinstance(raw, list):
                # 리스트 요소에 'id' 키가 있다면 그걸, 없다면 인덱스를 key로
                post_dict = {}
                for idx, item in enumerate(raw):
                    pid = item.get("id")
                    if pid is None:
                        pid = str(idx)
                    post_dict[str(pid)] = item
            elif isinstance(raw, dict):
                post_dict = raw
            else:
                raise ValueError("Post JSON은 list 또는 dict 이어야 합니다.")

            docs += make_post_docs(post_dict)

    # 2) TXT 처리
    if kind in ("txt", "all"):
        loader = DirectoryLoader(
            file_path,
            glob="**/*.txt",
            show_progress=True
        )
        docs += loader.load()

    if not docs:
        raise ValueError(f"'{kind}'에 해당하는 문서를 찾지 못했습니다.")

    return docs


# ---------- 2. 스플리터 ---------------------------------------
from langchain_text_splitters import RecursiveJsonSplitter

from tqdm.auto import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document


def split_docs_with_progress(
        docs: list[Document],
        chunk: int = 1000,
        overlap: int = 100,
) -> list[Document]:
    """
    각 Document를 순회하며 TextSplitter를 적용하고,
    tqdm으로 진행률을 표시합니다.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk,
        chunk_overlap=overlap,
        length_function=len_okt
    )
    all_chunks: list[Document] = []

    for doc in tqdm(docs, desc="문서 분할 중....", unit="doc"):
        # 각 Document마다 split_documents를 호출해도 되고,
        # 더 세밀하게는 splitter.split_text(doc.page_content)
        chunks = splitter.split_documents([doc])
        all_chunks.extend(chunks)

    return all_chunks


# ---------- 3. 임베딩 & DB ------------------------------------
# 1) 임베딩 ─────────────────────────────────────────────
# pip install -U langchain-huggingface
from langchain_huggingface import HuggingFaceEmbeddings


def load_embed(device: str, model_name: str):
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device},
        encode_kwargs={"normalize_embeddings": True},
    )


# 2) Chroma DB ─────────────────────────────────────────
from langchain_chroma import Chroma
from pathlib import Path

from pathlib import Path
from langchain_chroma import Chroma

from pathlib import Path
from tqdm.auto import tqdm
from langchain_chroma import Chroma


def get_db(docs, embed, persist_dir: str):
    """
    ▶ docs: list[Document]
    ▶ embed: embedding function
    ▶ persist_dir: 저장할 폴더 경로
    """
    persist_path = Path(persist_dir)
    persist_path.mkdir(parents=True, exist_ok=True)

    # 1) 기존 DB 로드
    if any(persist_path.iterdir()):
        print("▶ 기존 Chroma DB 로드")
        db = Chroma(persist_directory=str(persist_path), embedding_function=embed)

    # 2) 새 DB 생성
    else:
        print("▶ 새 Chroma DB 생성 (임베딩 + 저장)")
        db = Chroma(persist_directory=str(persist_path), embedding_function=embed)

        # tqdm 으로 프로그레스 바 표시하며 문서 추가
        for doc in tqdm(docs, desc="문서 추가 중", unit="doc"):
            db.add_documents([doc])

        # langchain_chroma 에서는 db.persist() 가 없으므로
        # 내부 클라이언트에 persist() 를 호출합니다.
        db._client.persist()

    return db


# 사용 예
# db = get_db(documents, embedding_fn, "my_chroma_db")
# 이후 추가 삽입 등 변경이 있으면:
# db.add_documents(new_docs)
# db.persist()


# ---------- 4. Retriever --------------------------------------
def build_retriever(mode: int, k: int, db, docs):
    vec = db.as_retriever(search_kwargs={"k": k})
    bm = BM25Retriever.from_documents(docs, preprocess_func=okt_tokenize);
    bm.k = k
    if mode == 1: return vec
    if mode == 2: return bm
    if mode == 3: return EnsembleRetriever(retrievers=[vec, bm], weights=[0.5, 0.5])
    raise ValueError("retriever_num 은 1~3")


# ---------- 5. LLM --------------------------------------------
def load_llm(engine: int, backend: int):
    if engine == 1:
        name = "gpt-4o-mini"
    elif engine == 2:
        name = "gemma3:4b"
    elif engine == 3:
        name = "qwen3:4b"
    else:
        raise ValueError("engine_num 은 1~3")

    if backend == 1:
        return ChatOpenAI(model=name, temperature=0,
                          streaming=True,
                          callbacks=[StreamingStdOutCallbackHandler()],
                          )
    elif backend == 2:
        return ChatOllama(model=name, temperature=0,
                          streaming=True,
                          callbacks=[StreamingStdOutCallbackHandler()],
                          )
    else:
        raise ValueError("1,2번 중 선택해 주세요.")


# ---------- 6. Chain ------------------------------------------
prompt_content = """
            You are an assistant for question-answering tasks.
            Use the following pieces of retrieved context to answer the question.
            If you don't know the answer, just say that you don't know.

            Answer in Korean.

            #Context:
            {context}
            """

PROMPT = ChatPromptTemplate.from_messages([

    (
        "system",
        prompt_content,
    ), ("human", "{question}"),

])


def build_chain(retriever, llm):
    format_docs = lambda ds: "\n\n".join(d.page_content for d in ds)
    chain = {
                "context": retriever | RunnableLambda(format_docs),
                "question": RunnablePassthrough(),
            } | PROMPT | llm | StrOutputParser()
    return chain



# --------------- main -----------------------------------------
def main(return_chain_only=False):
    # ----- ① 환경 변수 로드 ---------------------------------
    if os.path.exists("../../.env"):
        load_env_variables_for_Local()  # 로컬 실행
    else:
        load_env_variables_for_Colab()  # Colab 실행

    # ----- ② 파일 로드 -------------------------------------
    FILE_PATH = "../../Data_Files"
    docs = load_files(FILE_PATH, kind := input("파일 종류(json/txt/all): "))

    chunk_size = int(input("청크 사이즈(기본 1000): "))
    overlap_size = int(input("오버랩 사이즈(기본 50): "))
    docs = split_docs_with_progress(docs, chunk=chunk_size, overlap=overlap_size)

    device = {1: "mps", 2: "cuda", 3: "cpu"}[int(input("디바이스(1:mps/2:cuda/3:cpu): "))]
    embed = load_embed(device, "nlpai-lab/KURE-v1")
    db = get_db(docs, embed, f"./{kind}_{chunk_size}")

    mode = int(input("retriever (1 vec / 2 bm25 /3 ensemble): "))
    k = int(input("k 개수를 입력해 주세요: "))
    retr = build_retriever(mode, k=k, db=db, docs=docs)

    llm_model = int(input("LLM 모델 번호(1: gpt-4o-mini / 2: gemma3:4b / 3: qwen3:4b): "))
    llm = load_llm(llm_model, backend=int(input("LLM (1 openai / 2 ollama): ")))
    chain = build_chain(retr, llm)


    if return_chain_only:
        return chain

    while True:
        q = input("\n질문(종료 exit): ")
        if q.lower() == "exit":
            break
        print(chain.invoke(q))

if __name__ == "__main__":
    main()
