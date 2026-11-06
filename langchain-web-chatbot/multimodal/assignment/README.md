# PDF 추출 및 멀티모달 요약

PDF에서 텍스트, 표, 이미지를 추출하고 OpenAI `gpt-4o-mini`로 검색용 요약을 생성합니다. 현재 `main.py`는 추출과 요약 결과 저장까지 수행합니다.

## 설치 및 설정

### 1. 가상환경 생성 및 활성화

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux에서는 다음 명령으로 활성화합니다.

```bash
source .venv/bin/activate
```

VS Code를 사용한다면 `Python: Select Interpreter`에서 생성한 `.venv`를 선택하세요.

### 2. 패키지 설치

```powershell
python -m pip install -r requirements.txt
```

버전이 고정된 패키지 목록으로 설치하려면 위 명령 대신 다음을 사용하세요.

```powershell
python -m pip install -r requirements.lock.txt
```

### 3. API 키 설정

`.env`가 없다면 예제 파일을 복사합니다. 기존 `.env`가 있으면 복사하지 않고 내용을 확인하세요.

```powershell
Copy-Item .env.example .env
```

`assignment/.env`에 실제 키를 입력합니다.

```dotenv
OPENAI_API_KEY=실제_API_키
```

요약 시 PDF의 텍스트·표·이미지가 OpenAI API로 전송되며 API 사용 비용이 발생합니다.

### 4. PDF 준비

`data` 폴더에 다음 파일을 넣습니다.

```text
2020+인구주택총조사+표본+집계+결과+인구가구+기본+항목+보도자료(배포용).pdf
```

다른 PDF를 사용하려면 `main.py`의 `fname`을 변경하세요.

## 실행

```powershell
python main.py
```

실행 순서는 PDF 추출 → 텍스트 분할 → 추출 결과 저장 → API 키 확인 → 텍스트·표·이미지 요약 → 요약 결과 저장입니다.

## 파일 및 결과

| 경로 | 역할 |
| --- | --- |
| `main.py` | 전체 처리 흐름 실행 |
| `extract.py` | PDF 요소 추출 및 텍스트·표 분류 |
| `summarize_generate.py` | 텍스트·표·이미지 요약 및 이미지 Base64 인코딩 |
| `data/figures/` | 추출한 이미지 |
| `data/processed/extracted.pkl` | `texts`, `tables`, `texts_2k_token` 저장 |
| `data/processed/summaries.pkl` | `text_summaries`, `table_summaries`, `image_summaries`, `img_base64_list` 저장 |

재실행하면 PDF를 다시 추출하고 두 `.pkl` 파일을 덮어씁니다. 기존 추출 결과를 불러와 추출을 건너뛰는 기능은 현재 없습니다.

## 실행 문제 확인

- `ModuleNotFoundError`: 위에서 확인한 Python 환경에 `python -m pip install -r requirements.txt`로 설치했는지 확인하세요.
- PDF 관련 파일 오류: `data`의 실제 파일명과 `fname`이 같은지 확인하세요.
- `data/figures` 관련 오류: 이미지 추출 여부와 폴더 생성 여부를 확인하세요. 현재 이미지 요약 함수는 이 폴더가 존재한다고 가정합니다.
- PDF 변환·OCR 관련 오류: `unstructured`의 `hi_res` 추출에는 Python 패키지 외에 Poppler, Tesseract 같은 시스템 도구가 필요할 수 있습니다. 오류 메시지에 표시된 도구의 설치와 PATH를 확인하세요.
- 인증 오류: `assignment/.env`의 `OPENAI_API_KEY`를 확인하세요.

