import os
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import base64
from langchain_core.messages import HumanMessage


def generate_text_summaries(texts, tables, summarize_texts=False):

    prompt_text = """You are an assistant tasked with summarizing tables and text for retrieval.
    # These summaries will be embedded and used to retrieve the raw text or table elements.
    # Give a concise summary of the table or text that is well optimized for retrieval.
    # Table or text: {element}"""

    prompt = ChatPromptTemplate.from_template(prompt_text)
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    summarize_chain = {"element" : lambda x: x} | prompt | model | StrOutputParser()

    text_summaries = []
    table_summaries = []

    if texts and summarize_texts:
        text_summaries = summarize_chain.batch(texts, config={"max_concurrent": 5})
    elif texts and not summarize_texts:
        text_summaries = texts


    if tables:
        table_summaries = summarize_chain.batch(tables, config={"max_concurrent": 5})
    
    return text_summaries, table_summaries

def encode_image(image_path):
    """
    이미지를 base64로 인코딩
    """
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
    return img_base64

def image_summarize(img_base64, prompt):

    chat = ChatOpenAI(model="gpt-4o-mini", max_tokens=1024)
    message = HumanMessage(content=[{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base64}"}}, {"type": "text", "text": prompt}])
    response = chat.invoke([message])

    return response.content

def generate_img_summaries(path):

    img_base64_list = []
    image_summaries = []

    prompt_kor = """
    You are an assistant tasked with summarizing images for retrieval.
    These summaries will be embedded and used to retrieve the raw image.
    Provide a concise summary of the image that is well optimized for retrieval.
    The summary should be written in Korean (Hangul).
    """

    for file in sorted(os.listdir(path)):
        if file.lower().endswith((".jpg", ".jpeg", ".png")):
            image_path = os.path.join(path, file)
            img_base64 = encode_image(image_path)
            img_base64_list.append(img_base64)
            summary = image_summarize(img_base64, prompt_kor)
            image_summaries.append(summary)

    return img_base64_list, image_summaries
