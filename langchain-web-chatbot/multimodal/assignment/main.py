from pathlib import Path
import os
from extract import extract_pdf_elements, categorize_elements
from langchain_text_splitters import CharacterTextSplitter
import pickle
from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError
from summarize_generate import generate_text_summaries, encode_image, image_summarize, generate_img_summaries

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

