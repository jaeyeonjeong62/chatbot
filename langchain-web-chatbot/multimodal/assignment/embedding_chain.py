import re
import uuid
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage


def add_documents(retriever, doc_summaries, doc_contents):
    """요약본은 벡터DB에, 원본은 docstore에 '같은 id'로 저장합니다."""
    
    doc_ids = [str(uuid.uuid4()) for _ in doc_contents]
    
    summary_docs = [
        Document(page_content=s, metadata={retriever.id_key:doc_ids[i]})
        for i, s in enumerate(doc_summaries)
    ]

    retriever.vectorstore.add_documents(summary_docs)
    retriever.docstore.mset(list(zip(doc_ids, doc_contents)))

def split_image_text_types(docs):
    """검색 결과를 Base64 이미지와 텍스트로 나눕니다."""
    b64_images = []
    texts_out = []
    
    for doc in docs:
        doc = doc.page_content if isinstance(doc, Document) else doc
        if re.match("^[A-Za-z0-9+/]{100,}={0,2}$", doc):
            b64_images.append(doc)
        else:
            texts_out.append(doc)
    
    return {"images": b64_images, "texts": texts_out}

def img_prompt_func(data_dict):
    """검색된 원본을 멀티모달 LLM이 읽을 형태로 조립합니다."""
    messages = []
    
    for image in data_dict["context"]["images"]:
        messages.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image}"},
        })
        
    formatted_texts = "\n".join(data_dict["context"]["texts"])
    messages.append({
        "type": "text",
        "text": (
            "아래 자료를 근거로 질문에 한국어로 답하세요.\n"
            "자료에 없는 내용은 모른다고 답하세요.\n\n"
            f"질문: {data_dict['question']}\n\n"
            f"참고 텍스트:\n{formatted_texts}"
        ),
    })
    
    return [HumanMessage(content=messages)]