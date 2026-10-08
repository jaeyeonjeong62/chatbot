## Pydantic 친절하게 이해하기

### Pydantic이 뭔가요?

Pydantic은 LangChain과 별개의 라이브러리.
Python에서 데이터 검증을 강력하게 만드는 도구.

> "Python 클래스에 자동 검증 기능을 추가하는 라이브러리"

### 일반 Python으로 데이터 표현하기

#### 방법 1: dict 사용

```python
person = {
    "name": "현대",
    "age": 30,
    "email": "hyundai@example.com"
}

print(person["name"])    # 현대
print(person["age"])      # 30
```

```python
# 문제 1: 오타가 발생해도 모름
person = {"name": "현대", "age": 30, "emial": "hyundai@example.com"}  # email 오타!
print(person["email"])    # KeyError 발생, 디버깅 어려움

# 문제 2: 잘못된 타입도 허용
person = {"name": "현대", "age": "삼십"}  # age가 문자열?
# 그냥 들어감... 나중에 계산할 때 에러

# 문제 3: 필수 필드 빠뜨림
person = {"name": "현대"}  # age, email 빠짐
# 그래도 통과
```

#### 방법 2: 일반 Python 클래스

```python
class Person:
    def __init__(self, name, age, email):
        self.name = name
        self.age = age
        self.email = email

person = Person("현대", 30, "hyundai@example.com")
print(person.name)    # 현대
```

```python
# 여전히 잘못된 타입 허용
person = Person("현대", "삼십", "hyundai@example.com")  # OK?
```

#### 방법 3: Pydantic 사용 ⭐

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    email: str

# 정상 생성
person = Person(name="현대", age=30, email="hyundai@example.com")
print(person.name)    # 현대

# 자동 변환
person = Person(name="현대", age="30", email="hyundai@example.com")
# 문자열 "30"을 정수 30으로 자동 변환

# 잘못된 타입 → 에러!
person = Person(name="현대", age="삼십", email="hyundai@example.com")
# ValidationError: 정수로 변환 불가능
```

### Pydantic 핵심 문법 5가지

#### 문법 1: BaseModel 상속

```python
from pydantic import BaseModel

class MyData(BaseModel):
    field1: str
    field2: int
```

#### 문법 2: 타입 힌트로 필드 정의

```python
class Product(BaseModel):
    name: str                   # 문자열
    price: int                  # 정수
    in_stock: bool              # True/False
    tags: list[str]             # 문자열 리스트
    rating: float               # 실수
```

#### 문법 3: Field로 설명 추가

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(description="제품명")
    price: int = Field(
        description="가격 (원 단위)",
        ge=0,                      # greater or equal (최소값)
        le=10_000_000              # less or equal (최대값)
    )
```

#### 문법 4: Literal로 선택지 제한 ⭐

```python
from typing import Literal

class Order(BaseModel):
    status: Literal["pending", "shipped", "delivered", "cancelled"]
```

```python
order = Order(status="pending")        # OK
order = Order(status="processing")     # 에러! 정의된 4개 중 하나만 가능
```

#### 문법 5: Optional로 선택 필드

```python
from typing import Optional

class Profile(BaseModel):
    name: str                              # 필수
    bio: Optional[str] = None              # 선택 (없어도 OK)
```

`Optional[X]`는 "X 타입이거나 None이거나" 를 의미한다.

#### 실전 예시: 리뷰 분석용 스키마

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

class ReviewAnalysis(BaseModel):
    """리뷰 분석 결과"""

    rating: int = Field(
        description="평점 (1-5점)",
        ge=1,
        le=5
    )

    sentiment: Literal["positive", "negative", "neutral"] = Field(
        description="감정 (positive/negative/neutral)"
    )

    keywords: list[str] = Field(
        description="핵심 키워드 3개"
    )

    summary: str = Field(
        description="한 문장 요약"
    )

    is_recommend: Optional[bool] = Field(
        default=None,
        description="작성자가 추천하는지 여부 (불명확하면 None)"
    )
```

- ✅ rating은 항상 1-5 사이의 정수
- ✅ sentiment는 항상 3가지 중 하나
- ✅ keywords는 항상 문자열 리스트
- ✅ summary는 항상 문자열
- ✅ is_recommend는 True/False/None 중 하나

## OutputParser - LLM과 Pydantic 연결

### OutputParser가 하는 일

OutputParser는 **LLM의 텍스트 답변을 정형 데이터로 변환**하는 도구

```
[LLM 답변]
"이 리뷰의 평점은 5점이고 긍정적입니다..."
       ↓
[OutputParser]
       ↓
[Pydantic 객체]
ReviewAnalysis(rating=5, sentiment="positive", ...)
```

OutputParser는 LangChain이 제공하는 클래스.

### PydanticOutputParser가 하는 두 가지 일

#### 일 1: LLM에게 형식 지시문 만들어주기

**지시문을 자동 생성**

```python
from langchain_core.output_parsers import PydanticOutputParser

parser = PydanticOutputParser(pydantic_object=ReviewAnalysis)
print(parser.get_format_instructions())
```

출력 (긴 텍스트, 일부만):

```
The output should be formatted as a JSON instance that conforms to the JSON schema below.

Here is the output schema:
{
  "properties": {
    "rating": {"description": "평점 (1-5점)", "minimum": 1, "maximum": 5, "type": "integer"},
    "sentiment": {"description": "감정...", "enum": ["positive", "negative", "neutral"]},
    "keywords": {"description": "핵심 키워드 3개", "type": "array"},
    ...
  },
  "required": ["rating", "sentiment", "keywords", "summary"]
}
```

이 지시문을 LLM에게 같이 보내면, **LLM이 이 형식대로 JSON으로 답변**한다.

#### 일 2: JSON 답변을 Pydantic 객체로 파싱

```python
# LLM이 보낸 텍스트
llm_text = '{"rating": 5, "sentiment": "positive", "keywords": ["카메라"]}'

# 파서가 변환
analysis = parser.parse(llm_text)
print(type(analysis))          # ReviewAnalysis
print(analysis.rating)         # 5
```

### 체인에 파서 붙이기

```python
chain = prompt | llm | parser
```

```
사용자 입력
    ↓ {review: "..."}
[ prompt ] - 형식 지시문 + 사용자 입력 결합
    ↓ 메시지 객체
[ llm ] - JSON 형식 답변 생성
    ↓ "{"rating": 5, ...}" (텍스트)
[ parser ] - JSON → Pydantic 객체 변환
    ↓
ReviewAnalysis 객체!
```

```python
result = chain.invoke({"review": "이 카메라 좋아요!"})

# result는 ReviewAnalysis 객체
print(result.rating)          # 5 (정수)
print(result.sentiment)       # "positive" (문자열)
print(result.keywords)        # ["카메라"] (리스트)
```

## 전체 패턴 정리

```python
from pydantic import BaseModel, Field
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# === 1단계: 스키마 정의 ===
class MySchema(BaseModel):
    field1: int = Field(description="...")
    field2: Literal["a", "b", "c"]

# === 2단계: 파서 생성 ===
parser = PydanticOutputParser(pydantic_object=MySchema)

# === 3단계: 프롬프트 (형식 지시문 자동 삽입) ===
prompt = ChatPromptTemplate.from_messages([
    ("system", "...{format_instructions}"),
    ("human", "{input}")
]).partial(format_instructions=parser.get_format_instructions())

# === 4단계: LLM (temperature=0) ===
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# === 5단계: 체인 ===
chain = prompt | llm | parser

# 사용
result = chain.invoke({"input": "..."})
print(result.field1)  # 객체로 접근!
```

### 주의 1: temperature는 반드시 0

### 주의 2: Field description은 필수

```python
# ❌ description 없음 → LLM이 추측해서 채움
class Bad(BaseModel):
    score: int

# ✅ description 있음 → LLM이 정확히 이해
class Good(BaseModel):
    score: int = Field(description="0-100 사이의 만족도 점수")
```

### 주의 3: Literal로 선택지 제한

```python
# ❌ 자유 텍스트
class Bad(BaseModel):
    sentiment: str
# → "positive", "긍정적", "happy", "좋음" 등 마음대로

# ✅ Literal 사용
class Good(BaseModel):
    sentiment: Literal["positive", "negative", "neutral"]
# → 이 3개 중 하나만!
```

### 주의 4: .partial() 활용

```python
# ❌ 매번 직접 전달
chain.invoke({
    "format_instructions": parser.get_format_instructions(),
    "input": "..."
})

# ✅ .partial()로 미리 채움
prompt = prompt.partial(format_instructions=parser.get_format_instructions())
chain.invoke({"input": "..."})  # 깔끔!
```

---

## 핵심 코드 패턴

```python
# 1. 스키마
class MySchema(BaseModel):
    field1: int = Field(description="...")
    field2: Literal["a", "b", "c"]

# 2. 파서
parser = PydanticOutputParser(pydantic_object=MySchema)

# 3. 프롬프트
prompt = ChatPromptTemplate.from_messages([
    ("system", "...{format_instructions}"),
    ("human", "{input}")
]).partial(format_instructions=parser.get_format_instructions())

# 4. LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 5. 체인
chain = prompt | llm | parser
result = chain.invoke({"input": "..."})
```

