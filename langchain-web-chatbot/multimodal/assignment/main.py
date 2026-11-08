from pathlib import Path
import os
import gradio as gr
from extract import extract_pdf_elements, categorize_elements
from langchain_text_splitters import CharacterTextSplitter
import pickle
from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError
from summarize_generate import generate_text_summaries, encode_image, image_summarize, generate_img_summaries
from langchain_chroma import Chroma
try:
    from langchain_classic.retrievers.multi_vector import MultiVectorRetriever
except:
    print("MultiVectorRetriever 클래스가 필요합니다.")

try:
    from langchain_core.stores import InMemoryStore
except:
    print("InMemoryStore 클래스가 필요합니다.")
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from embedding_chain import *


PROJECT_ROOT = Path(__file__).resolve().parent
fname = "2020+인구주택총조사+표본+집계+결과+인구가구+기본+항목+보도자료(배포용).pdf"
pdf_path = PROJECT_ROOT / "data" / fname
figures_dir = pdf_path.parent / "figures"

raw_pdf_elements = extract_pdf_elements(pdf_path)
tables, texts = categorize_elements(raw_pdf_elements)

if figures_dir.exists():
    image_files = sorted([f for f in figures_dir.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
else:
    image_files = []

text_splitter = CharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=2000,
    chunk_overlap=200,
)

joined_text = " ".join(texts)
texts_2k_token = text_splitter.split_text(joined_text)

output_dir = Path(PROJECT_ROOT) / "data" / "processed"
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_dir / "extracted.pkl", "wb") as f:
    pickle.dump({"texts": texts, "tables": tables, "texts_2k_token": texts_2k_token}, f)

load_dotenv(PROJECT_ROOT / ".env")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다. .env 파일을 확인하세요.")

try:
    client = OpenAI(api_key=openai_api_key)
    client.models.list()
except AuthenticationError:
    raise ValueError("OpenAI API 키가 유효하지 않습니다. .env 파일을 확인하세요.")

if not texts:
    pkl_path = PROJECT_ROOT / "data" / "processed" / "extracted.pkl"
    with open(pkl_path, "rb") as f:
        data = pickle.load(f)
    texts = data["texts"]
    tables = data["tables"]
    texts_2k_token = data["texts_2k_token"]

text_summaries, table_summaries = generate_text_summaries(texts_2k_token, tables, summarize_texts=True)
img_base64_list, image_summaries = generate_img_summaries(str(figures_dir))

output_dir = PROJECT_ROOT / "data" / "processed"
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_dir / "summaries.pkl", "wb") as f:
    pickle.dump({
        "text_summaries": text_summaries,
        "table_summaries": table_summaries,
        "image_summaries": image_summaries,
        "img_base64_list": img_base64_list}, f)

vectorstore = Chroma(
    collection_name="multimodal_rag", embedding_function=OpenAIEmbeddings(model="text-embedding-3-small")
)
store = InMemoryStore()
id_key = "doc_id"

retriever = MultiVectorRetriever(
    vectorstore= vectorstore, docstore= store, id_key = id_key
)

if text_summaries:
    add_documents(retriever, text_summaries, texts_2k_token)
if table_summaries:
    add_documents(retriever, table_summaries, tables)
if image_summaries:
    add_documents(retriever, image_summaries, img_base64_list)

model = ChatOpenAI(temperature=0, model="gpt-4o-mini", max_tokens=1024)

chain = (
    {
        "context": retriever | RunnableLambda(split_image_text_types),
        "question": RunnablePassthrough(),
    }
    | RunnableLambda(img_prompt_func)
    | model
    | StrOutputParser()
)


def chat_fn(message, history):
    # 현재 체인은 이전 대화 기록 없이 이번 질문으로 자료를 검색합니다.
    return chain.invoke(message)


if __name__ == "__main__":
    demo = gr.ChatInterface(
        fn=chat_fn,
        title="반려동물 키우는 사람들의 특징",
        description="보고서의 텍스트·표·이미지를 바탕으로 질문에 답합니다. 각 질문은 독립적으로 처리합니다.",
        examples=[
            "이 보고서의 주요 내용을 요약해줘",
            "1인 가구의 주요 특징을 설명해줘",
            "보고서의 표와 그래프에서 드러나는 인구 변화를 설명해줘",
        ],
    )
    demo.launch()
