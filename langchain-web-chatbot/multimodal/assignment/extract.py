from pathlib import Path
from unstructured.partition.pdf import partition_pdf


def extract_pdf_elements(path):
    """
    PDF 파일에서 이미지, 테이블, 텍스트 블록을 추출
    """

    return partition_pdf(
        filename=path,
        strategy="hi_res",
        extract_images_in_pdf=True,
        infer_table_structure=True,
        chunking_strategy="by_title",
        max_characters=4000,
        new_after_n_chars=3800,
        combine_text_under_n_chars=2000,
        extract_image_block_output_dir=str(Path(path).parent / "figures")
    )

def categorize_elements(raw_pdf_elements):
    """
    PDF에서 추출한 요소들을 테이블과 텍스트로 분류
    """

    tables = []
    texts = []

    for element in raw_pdf_elements:
        if "Table" in str(type(element)):
            tables.append(str(element))
        elif "CompositeElement" in str(type(element)):
            texts.append(str(element))
            
    return tables, texts