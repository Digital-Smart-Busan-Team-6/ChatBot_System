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
def load_files(folder: str, kind: str) -> list[Document]:
    docs: list[Document] = []

    if kind in ("json", "all"):
        for p in Path(folder).rglob("*.json"):
            with p.open(encoding="utf-8") as f:
                txt = json.dumps(json.load(f), ensure_ascii=False, indent=2)
            docs.append(Document(page_content=txt, metadata={"source": p.as_posix()}))

    if kind in ("txt", "all"):
        docs.extend(DirectoryLoader(folder, glob="**/*.txt").load())

    if not docs:
        raise ValueError("파일을 찾지 못했습니다.")

    print(f"파일 {len(docs)}개 로드 완료")
    print(f"파일 종류: {kind}")
    return docs


# ---------- 2. 스플리터 ---------------------------------------
def split_docs(docs: list[Document], kind: str,
               chunk: int = 1000, overlap: int = 100):
    if kind == "json":
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk, chunk_overlap=overlap, length_function=len_okt
        )
        flat = [d.page_content for d in docs]
        return splitter.create_documents(flat)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk, chunk_overlap=overlap, length_function=len_okt
    )
    return splitter.split_documents(docs)


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


def get_db(texts, embed, persist_dir: str):
    persist_dir = Path(persist_dir)
    if persist_dir.exists():
        print("기존 Chroma DB 로드")
        return Chroma(persist_directory=str(persist_dir), embedding_function=embed)

    print("새 Chroma DB 생성")
    return Chroma.from_documents(
        texts,
        embed,
        persist_directory=str(persist_dir)
    )


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
        name = "quen3:4b"
    else:
        raise ValueError("engine_num 은 1~3")
    if backend == 1:
        return ChatOpenAI(model=name, temperature=0,
                          streaming=True,
                          callbacks=[StreamingStdOutCallbackHandler()],
                          )
    return ChatOllama(model=name, temperature=0,
                      streaming=True,
                      callbacks=[StreamingStdOutCallbackHandler()],
                      )


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

    kind = input("파일 형식(json/txt): ").strip()
    folder = "../../Data_Files"
    docs = load_files(folder, kind)

    chunk = int(input("chunk: "))
    texts = split_docs(docs, kind, chunk)

    device = {1: "mps", 2: "cuda", 3: "cpu"}[int(input("디바이스(1:mps/2:cuda/3:cpu): "))]
    embed = load_embed(device, "nlpai-lab/KURE-v1")
    db = get_db(texts, embed, f"./{kind}_{chunk}")

    mode = int(input("retriever (1 vec / 2 bm25 /3 ensemble): "))
    k = int(input("k 개수를 입력해 주세요: "))
    retr = build_retriever(mode, k=k, db=db, docs=texts)

    llm_model = int(input("LLM 모델 번호(1: gpt-4o-mini / 2: gemma3:4b / 3: quen3:4b): "))
    llm = load_llm(llm_model_num := llm_model, backend=int(input("LLM (1 openai / 2 ollama): ")))
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
